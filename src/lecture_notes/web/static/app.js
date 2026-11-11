let globalLoadingCount = 0;

function showGlobalLoading() {
  globalLoadingCount += 1;
  const indicator = document.getElementById("globalLoadingIndicator");
  if (indicator) indicator.hidden = false;
}

function hideGlobalLoading() {
  globalLoadingCount = Math.max(0, globalLoadingCount - 1);
  const indicator = document.getElementById("globalLoadingIndicator");
  if (indicator && globalLoadingCount === 0) indicator.hidden = true;
}

const nativeFetch = window.fetch.bind(window);
async function withGlobalLoading(action) {
  showGlobalLoading();
  try {
    return await action();
  } finally {
    hideGlobalLoading();
  }
}

window.fetch = (...arguments_) => {
  return withGlobalLoading(() => nativeFetch(...arguments_));
};

function waitForGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + 10000;
    const check = () => {
      if (window.google?.accounts?.id) return resolve();
      if (Date.now() >= deadline) return reject(new Error("google-unavailable"));
      window.setTimeout(check, 50);
    };
    check();
  });
}

function showGoogleLoginMessage(mount, message) {
  const element = document.getElementById("googleLoginMessage");
  if (!element) return;
  element.textContent = message || mount.dataset.loginFailed || "";
  element.hidden = false;
}

async function initializeGoogleLogin(mount) {
  try {
    const [configResponse, config] = await withGlobalLoading(async () => {
      const response = await nativeFetch("/api/auth/google/config", { credentials: "same-origin" });
      return [response, await response.json()];
    });
    if (!configResponse.ok || !config.enabled || !config.client_id) {
      showGoogleLoginMessage(mount, mount.dataset.notConfigured);
      return;
    }
    await waitForGoogleIdentity();
    window.google.accounts.id.initialize({
      client_id: config.client_id,
      callback: async (googleResponse) => {
        try {
          if (!googleResponse?.credential) throw new Error(mount.dataset.loginFailed);
          const [response, payload] = await withGlobalLoading(async () => {
            const loginResponse = await nativeFetch("/api/auth/google", {
              method: "POST",
              credentials: "same-origin",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id_token: googleResponse.credential }),
            });
            return [loginResponse, await loginResponse.json().catch(() => ({}))];
          });
          if (!response.ok) throw new Error(payload.message || mount.dataset.loginFailed);
          showGlobalLoading();
          window.location.assign("/");
        } catch (error) {
          showGoogleLoginMessage(mount, error.message);
        }
      },
    });
    window.google.accounts.id.renderButton(mount, {
      theme: "outline",
      size: "large",
      text: "signin_with",
      shape: "rectangular",
    });
  } catch (_error) {
    showGoogleLoginMessage(mount, mount.dataset.loginFailed);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("submit", () => showGlobalLoading());
  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("a[href]");
    if (!link || link.target || link.hasAttribute("download")) return;
    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || url.pathname.endsWith("/download")) return;
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return;
    showGlobalLoading();
  });
  document.querySelectorAll("time.local-time").forEach((element) => {
    const value = new Date(element.dateTime);
    if (!Number.isNaN(value.getTime())) element.textContent = value.toLocaleString("et-EE");
  });
  const browserDateTimeFormatter = new Intl.DateTimeFormat("et-EE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  document.querySelectorAll("time.browser-date-time").forEach((element) => {
    const value = new Date(element.dateTime);
    if (Number.isNaN(value.getTime())) return;
    const parts = Object.fromEntries(
      browserDateTimeFormatter.formatToParts(value).map((part) => [part.type, part.value]),
    );
    element.textContent = `${parts.day}.${parts.month}.${parts.year} ${parts.hour}:${parts.minute}:${parts.second}`;
  });
  document.querySelectorAll("[data-resolve-source]").forEach((source) => {
    const button = source.closest("form")?.querySelector("[data-resolve-button]");
    if (!button) return;
    const update = () => {
      button.disabled = !source.value.trim();
    };
    source.addEventListener(source.tagName === "SELECT" ? "change" : "input", update);
    update();
  });
  const googleLoginMount = document.getElementById("googleLoginMount");
  if (googleLoginMount) initializeGoogleLogin(googleLoginMount);
  document.querySelectorAll(".slide-file-input").forEach((input) => {
    input.addEventListener("change", () => {
      const filename = input.closest(".slide-upload")?.querySelector(".slide-file-name");
      if (filename) filename.textContent = input.files?.[0]?.name || "";
    });
  });
  const createSubmissionForm = document.getElementById("createSubmissionForm");
  const submitJobsButton = document.getElementById("submitJobsButton");
  const submissionProgress = document.getElementById("submissionProgress");
  if (createSubmissionForm && submitJobsButton && submissionProgress) {
    createSubmissionForm.addEventListener("submit", () => {
      submitJobsButton.disabled = true;
      submissionProgress.hidden = false;
    });
  }
  const transcriptViewer = document.getElementById("transcriptViewer");
  const openTranscriptViewer = document.getElementById("openTranscriptViewer");
  const closeTranscriptViewer = document.getElementById("closeTranscriptViewer");
  if (transcriptViewer && openTranscriptViewer && closeTranscriptViewer) {
    const videoContainer = document.getElementById("transcriptVideoContainer");
    const transcriptVideo = document.getElementById("transcriptVideo");
    const transcriptSecondaryVideo = document.getElementById("transcriptSecondaryVideo");
    const transcriptContent = document.getElementById("transcriptContent");
    const followTranscript = document.getElementById("followTranscript");
    const slideVersionSelect = document.getElementById("slideVersionSelect");
    const downloadSelectedVersion = document.getElementById("downloadSelectedVersion");
    const defaultSlideVersionOperationId = document.getElementById("defaultSlideVersionOperationId");
    const openDefaultSlideVersionDialog = document.getElementById("openDefaultSlideVersionDialog");
    const primaryVideoUrl = transcriptViewer.dataset.primaryVideoUrl;
    const secondaryVideoUrl = transcriptViewer.dataset.secondaryVideoUrl;
    let pendingVideoStart = null;
    let transcriptSegments = [];
    let activeSegment = null;
    let followingTranscript = true;
    let automaticScrollTimer = null;
    const timestampSeconds = (value) => {
      const parts = value.split(":").map((part) => Number.parseInt(part, 10));
      if (parts.length !== 3 || parts.some((part) => !Number.isFinite(part))) return null;
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    };
    const setFollowingTranscript = (enabled) => {
      followingTranscript = enabled;
      if (followTranscript) followTranscript.disabled = enabled;
    };
    const refreshTranscriptSegments = () => {
      activeSegment = null;
      transcriptSegments = [];
      transcriptContent?.querySelectorAll('a[href^="#video-at-"]').forEach((link) => {
        const match = link.textContent.match(/^(\d{2,}:\d{2}:\d{2})–(\d{2,}:\d{2}:\d{2})$/);
        const element = link.closest("p");
        if (!match || !element) return;
        const start = timestampSeconds(match[1]);
        const end = timestampSeconds(match[2]);
        if (start === null || end === null) return;
        element.classList.add("transcript-segment");
        transcriptSegments.push({ element, start, end });
      });
      transcriptSegments.sort((left, right) => left.start - right.start);
    };
    const scrollToActiveSegment = () => {
      if (!transcriptContent || !activeSegment) return;
      const contentRect = transcriptContent.getBoundingClientRect();
      const segmentRect = activeSegment.element.getBoundingClientRect();
      const comfortablyVisible = segmentRect.top >= contentRect.top + 24
        && segmentRect.bottom <= contentRect.bottom - 24;
      if (comfortablyVisible) return;
      window.clearTimeout(automaticScrollTimer);
      transcriptContent.classList.add("is-auto-scrolling");
      const top = transcriptContent.scrollTop
        + segmentRect.top - contentRect.top
        - (transcriptContent.clientHeight - segmentRect.height) / 2;
      transcriptContent.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
      automaticScrollTimer = window.setTimeout(() => {
        transcriptContent.classList.remove("is-auto-scrolling");
      }, 500);
    };
    const updateActiveSegment = (seconds, forceScroll = false) => {
      let selected = null;
      for (const segment of transcriptSegments) {
        if (segment.start > seconds) break;
        selected = segment;
      }
      if (selected !== activeSegment) {
        activeSegment?.element.classList.remove("is-current-segment");
        activeSegment = selected;
        activeSegment?.element.classList.add("is-current-segment");
      }
      if (activeSegment && (followingTranscript || forceScroll)) scrollToActiveSegment();
    };
    const hideVideo = () => {
      if (videoContainer) videoContainer.hidden = true;
    };
    const releaseVideo = () => {
      if (!transcriptVideo) return;
      [transcriptVideo, transcriptSecondaryVideo].forEach((video) => {
        if (!video) return;
        video.pause();
        video.removeAttribute("src");
        video.load();
      });
      pendingVideoStart = null;
      activeSegment?.element.classList.remove("is-current-segment");
      activeSegment = null;
      setFollowingTranscript(true);
      hideVideo();
    };
    const syncSecondaryVideo = () => {
      if (!transcriptSecondaryVideo || transcriptSecondaryVideo.hidden || transcriptSecondaryVideo.readyState < 1) return;
      if (Math.abs(transcriptSecondaryVideo.currentTime - transcriptVideo.currentTime) > 0.25) {
        transcriptSecondaryVideo.currentTime = transcriptVideo.currentTime;
      }
      transcriptSecondaryVideo.playbackRate = transcriptVideo.playbackRate;
    };
    const loadVideos = (seconds) => {
      pendingVideoStart = seconds;
      if (!transcriptVideo.getAttribute("src")) {
        transcriptVideo.src = primaryVideoUrl;
        transcriptVideo.load();
      }
      if (transcriptSecondaryVideo && secondaryVideoUrl && !transcriptSecondaryVideo.getAttribute("src")) {
        transcriptSecondaryVideo.hidden = false;
        videoContainer?.classList.remove("is-single-video");
        transcriptSecondaryVideo.src = secondaryVideoUrl;
        transcriptSecondaryVideo.load();
      }
      if (transcriptVideo.readyState >= 1) transcriptVideo.currentTime = seconds;
      if (transcriptSecondaryVideo?.readyState >= 1) transcriptSecondaryVideo.currentTime = seconds;
    };
    if (videoContainer && transcriptVideo && primaryVideoUrl) {
      transcriptVideo.addEventListener("loadedmetadata", () => {
        if (pendingVideoStart !== null) {
          transcriptVideo.currentTime = pendingVideoStart;
        }
      });
      transcriptSecondaryVideo?.addEventListener("loadedmetadata", () => {
        if (pendingVideoStart !== null) transcriptSecondaryVideo.currentTime = pendingVideoStart;
        syncSecondaryVideo();
        if (!transcriptVideo.paused) transcriptSecondaryVideo.play().catch(() => {});
      });
      transcriptSecondaryVideo?.addEventListener("error", () => {
        transcriptSecondaryVideo.hidden = true;
        videoContainer.classList.add("is-single-video");
      });
      transcriptVideo.addEventListener("play", () => {
        syncSecondaryVideo();
        transcriptSecondaryVideo?.play().catch(() => {});
      });
      transcriptVideo.addEventListener("pause", () => transcriptSecondaryVideo?.pause());
      transcriptVideo.addEventListener("seeking", syncSecondaryVideo);
      transcriptVideo.addEventListener("seeked", syncSecondaryVideo);
      transcriptVideo.addEventListener("ratechange", syncSecondaryVideo);
      transcriptVideo.addEventListener("timeupdate", () => {
        updateActiveSegment(transcriptVideo.currentTime);
        syncSecondaryVideo();
      });
      transcriptVideo.addEventListener("ended", () => transcriptSecondaryVideo?.pause());
    }
    if (transcriptContent) {
      refreshTranscriptSegments();
      ["wheel", "touchstart", "pointerdown"].forEach((eventName) => {
        transcriptContent.addEventListener(eventName, () => setFollowingTranscript(false), { passive: true });
      });
      transcriptContent.addEventListener("keydown", (event) => {
        if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(event.key)) {
          setFollowingTranscript(false);
        }
      });
      transcriptContent.addEventListener("click", (event) => {
        const timestampLink = event.target.closest('a[href^="#video-at-"]');
        if (timestampLink && videoContainer && transcriptVideo && primaryVideoUrl) {
          event.preventDefault();
          const seconds = Number.parseInt(timestampLink.getAttribute("href").slice("#video-at-".length), 10);
          if (!Number.isFinite(seconds)) return;
          videoContainer.hidden = false;
          setFollowingTranscript(true);
          loadVideos(seconds);
          updateActiveSegment(seconds, true);
          transcriptVideo.play().catch(() => {});
          return;
        }
        const image = event.target.closest("img");
        if (image) image.classList.toggle("is-expanded");
      });
      transcriptContent.addEventListener("keydown", (event) => {
        const image = event.target.closest("img");
        if (!image || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        image.classList.toggle("is-expanded");
      });
      transcriptContent.querySelectorAll("img").forEach((image) => { image.tabIndex = 0; });
    }
    followTranscript?.addEventListener("click", () => {
      setFollowingTranscript(true);
      updateActiveSegment(transcriptVideo?.currentTime || 0, true);
    });
    if (slideVersionSelect) {
      slideVersionSelect.addEventListener("change", async () => {
        const operationId = slideVersionSelect.value;
        const template = slideVersionSelect.dataset.urlTemplate;
        if (!operationId || !template || !transcriptContent) return;
        try {
          const [response, payload] = await withGlobalLoading(async () => {
            const versionResponse = await nativeFetch(
              template.replace("__operation_id__", encodeURIComponent(operationId)),
              { credentials: "same-origin" },
            );
            return [versionResponse, await versionResponse.json()];
          });
          if (!response.ok) throw new Error("slide-version-unavailable");
          releaseVideo();
          transcriptContent.innerHTML = payload.html;
          transcriptContent.querySelectorAll("img").forEach((image) => { image.tabIndex = 0; });
          refreshTranscriptSegments();
          if (downloadSelectedVersion) downloadSelectedVersion.href = payload.download_url;
          if (defaultSlideVersionOperationId) defaultSlideVersionOperationId.value = payload.operation_id === null ? "" : String(payload.operation_id);
          if (openDefaultSlideVersionDialog) openDefaultSlideVersionDialog.disabled = payload.is_original;
        } catch (_error) {
          showGlobalLoading();
          window.location.reload();
        }
      });
    }
    openTranscriptViewer.addEventListener("click", () => {
      transcriptViewer.showModal();
      document.body.classList.add("modal-open");
    });
    const closeViewer = () => transcriptViewer.close();
    closeTranscriptViewer.addEventListener("click", closeViewer);
    transcriptViewer.addEventListener("click", (event) => {
      if (event.target === transcriptViewer) closeViewer();
    });
    transcriptViewer.addEventListener("close", () => {
      releaseVideo();
      document.body.classList.remove("modal-open");
      transcriptContent?.querySelectorAll("img.is-expanded").forEach((image) => image.classList.remove("is-expanded"));
    });
  }
  const bindConfirmDialog = (dialogId, openId, cancelId) => {
    const dialog = document.getElementById(dialogId);
    const open = document.getElementById(openId);
    const cancel = document.getElementById(cancelId);
    if (!dialog || !open || !cancel) return;
    open.addEventListener("click", () => dialog.showModal());
    cancel.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  };
  bindConfirmDialog("deleteLectureDialog", "openDeleteLectureDialog", "cancelDeleteLecture");
  bindConfirmDialog("reprocessSlidesDialog", "openReprocessSlidesDialog", "cancelReprocessSlides");
  bindConfirmDialog("defaultSlideVersionDialog", "openDefaultSlideVersionDialog", "cancelDefaultSlideVersion");
  const originalVideoDialog = document.getElementById("originalVideoDialog");
  const openOriginalVideoDialog = document.getElementById("openOriginalVideoDialog");
  const closeOriginalVideoDialog = document.getElementById("closeOriginalVideoDialog");
  const originalLectureVideo = document.getElementById("originalLectureVideo");
  if (originalVideoDialog && openOriginalVideoDialog && closeOriginalVideoDialog && originalLectureVideo) {
    const releaseOriginalVideo = () => {
      originalLectureVideo.pause();
      originalLectureVideo.removeAttribute("src");
      originalLectureVideo.load();
      document.body.classList.remove("modal-open");
    };
    openOriginalVideoDialog.addEventListener("click", () => {
      originalVideoDialog.showModal();
      document.body.classList.add("modal-open");
      if (!originalLectureVideo.getAttribute("src")) {
        originalLectureVideo.src = originalVideoDialog.dataset.videoUrl;
        originalLectureVideo.load();
      }
    });
    closeOriginalVideoDialog.addEventListener("click", () => originalVideoDialog.close());
    originalVideoDialog.addEventListener("click", (event) => {
      if (event.target === originalVideoDialog) originalVideoDialog.close();
    });
    originalVideoDialog.addEventListener("close", releaseOriginalVideo);
  }
  if (!document.querySelector("[data-auto-refresh='true']")) return;
  const seconds = Number.parseInt(document.body.dataset.pollInterval || "0", 10);
  if (Number.isFinite(seconds) && seconds > 0) {
    const refreshWhenNoDialogIsOpen = () => {
      if (document.querySelector("dialog[open]")) {
        window.setTimeout(refreshWhenNoDialogIsOpen, seconds * 1000);
        return;
      }
      showGlobalLoading();
      window.location.reload();
    };
    window.setTimeout(refreshWhenNoDialogIsOpen, seconds * 1000);
  }
});

window.addEventListener("pageshow", () => {
  globalLoadingCount = 0;
  const indicator = document.getElementById("globalLoadingIndicator");
  if (indicator) indicator.hidden = true;
});
