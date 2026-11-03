-- TTU loengutranskriptsiooni rakenduse Oracle'i põhiskeem.
-- Käivita ttu_loeng skeemikasutajana SQL Developeris ühe skriptina.
-- Skript loob objektid tühja skeemi; olemasolevaid objekte see ei muuda.

CREATE SEQUENCE app_users_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE submissions_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE lecture_processings_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE uploads_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE background_operations_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE app_users (
    user_id NUMBER(19) DEFAULT app_users_seq.NEXTVAL NOT NULL,
    public_id VARCHAR2(36 CHAR) NOT NULL,
    identity_provider VARCHAR2(100 CHAR),
    external_subject VARCHAR2(255 CHAR),
    email VARCHAR2(320 CHAR),
    display_name VARCHAR2(250 CHAR),
    role_code VARCHAR2(30 CHAR) NOT NULL,
    enabled NUMBER(1) NOT NULL,
    start_date DATE DEFAULT SYSDATE NOT NULL,
    end_date DATE,
    created TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    CONSTRAINT app_users_pk PRIMARY KEY (user_id),
    CONSTRAINT app_users_public_id_uq UNIQUE (public_id),
    CONSTRAINT app_users_identity_uq UNIQUE (identity_provider, external_subject),
    CONSTRAINT app_users_email_uq UNIQUE (email),
    CONSTRAINT app_users_enabled_ck CHECK (enabled IN (0, 1))
);

CREATE TABLE submissions (
    submission_id NUMBER(19) DEFAULT submissions_seq.NEXTVAL NOT NULL,
    public_id VARCHAR2(36 CHAR) NOT NULL,
    user_id NUMBER(19),
    echo_public_url VARCHAR2(2000 CHAR) NOT NULL,
    echo_public_section_id VARCHAR2(36 CHAR) NOT NULL,
    echo_canonical_section_id VARCHAR2(36 CHAR) NOT NULL,
    course_title VARCHAR2(500 CHAR),
    resolver_manifest_path VARCHAR2(1000 CHAR) NOT NULL,
    start_date DATE DEFAULT SYSDATE NOT NULL,
    end_date DATE,
    created TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    CONSTRAINT submissions_pk PRIMARY KEY (submission_id),
    CONSTRAINT submissions_public_id_uq UNIQUE (public_id),
    CONSTRAINT submissions_user_fk FOREIGN KEY (user_id)
        REFERENCES app_users (user_id)
);

CREATE TABLE lecture_processings (
    lecture_processing_id NUMBER(19)
        DEFAULT lecture_processings_seq.NEXTVAL NOT NULL,
    public_id VARCHAR2(36 CHAR),
    submission_id NUMBER(19) NOT NULL,
    echo_lesson_id VARCHAR2(36 CHAR) NOT NULL,
    lecture_title VARCHAR2(500 CHAR),
    lecture_start_at TIMESTAMP,
    duration_seconds NUMBER(12,3),
    recording_status VARCHAR2(30 CHAR) NOT NULL,
    start_date DATE DEFAULT SYSDATE NOT NULL,
    end_date DATE,
    created TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    CONSTRAINT lecture_processings_pk PRIMARY KEY (lecture_processing_id),
    CONSTRAINT lecture_proc_public_id_uq UNIQUE (public_id),
    CONSTRAINT lecture_proc_sub_lesson_uq
        UNIQUE (submission_id, echo_lesson_id),
    CONSTRAINT lecture_proc_submission_fk FOREIGN KEY (submission_id)
        REFERENCES submissions (submission_id)
);

CREATE TABLE uploads (
    upload_id NUMBER(19) DEFAULT uploads_seq.NEXTVAL NOT NULL,
    public_id VARCHAR2(36 CHAR) NOT NULL,
    lecture_processing_id NUMBER(19) NOT NULL,
    upload_type VARCHAR2(30 CHAR) NOT NULL,
    original_filename VARCHAR2(500 CHAR) NOT NULL,
    stored_relative_path VARCHAR2(1000 CHAR) NOT NULL,
    media_type VARCHAR2(255 CHAR) NOT NULL,
    size_bytes NUMBER(19),
    sha256 CHAR(64 CHAR),
    start_date DATE DEFAULT SYSDATE NOT NULL,
    end_date DATE,
    created TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    CONSTRAINT uploads_pk PRIMARY KEY (upload_id),
    CONSTRAINT uploads_public_id_uq UNIQUE (public_id),
    CONSTRAINT uploads_stored_path_uq UNIQUE (stored_relative_path),
    CONSTRAINT uploads_lecture_fk FOREIGN KEY (lecture_processing_id)
        REFERENCES lecture_processings (lecture_processing_id)
);

CREATE UNIQUE INDEX uploads_active_type_uq
    ON uploads (
        CASE WHEN end_date IS NULL THEN lecture_processing_id END,
        CASE WHEN end_date IS NULL THEN upload_type END
    );

CREATE TABLE background_operations (
    operation_id NUMBER(19) DEFAULT background_operations_seq.NEXTVAL NOT NULL,
    public_id VARCHAR2(36 CHAR) NOT NULL,
    lecture_processing_id NUMBER(19) NOT NULL,
    previous_operation_id NUMBER(19),
    operation_type VARCHAR2(20 CHAR) NOT NULL,
    attempt_number NUMBER(9) NOT NULL,
    idempotency_key VARCHAR2(250 CHAR) NOT NULL,
    ords_job_id NUMBER(19),
    registration_error_code VARCHAR2(100 CHAR),
    registration_error_message VARCHAR2(2000 CHAR),
    ords_registered_at TIMESTAMP,
    local_started_at TIMESTAMP,
    local_completed_at TIMESTAMP,
    local_outcome VARCHAR2(30 CHAR),
    local_error_code VARCHAR2(100 CHAR),
    local_error_message VARCHAR2(2000 CHAR),
    start_date DATE DEFAULT SYSDATE NOT NULL,
    end_date DATE,
    created TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    last_updated TIMESTAMP,
    CONSTRAINT background_operations_pk PRIMARY KEY (operation_id),
    CONSTRAINT background_ops_public_id_uq UNIQUE (public_id),
    CONSTRAINT background_ops_lecture_op_uq
        UNIQUE (lecture_processing_id, operation_id),
    CONSTRAINT background_ops_attempt_uq
        UNIQUE (lecture_processing_id, operation_type, attempt_number),
    CONSTRAINT background_ops_idempotency_uq UNIQUE (idempotency_key),
    CONSTRAINT background_ops_ords_job_uq UNIQUE (ords_job_id),
    CONSTRAINT background_ops_lecture_fk FOREIGN KEY (lecture_processing_id)
        REFERENCES lecture_processings (lecture_processing_id),
    CONSTRAINT background_ops_previous_fk
        FOREIGN KEY (lecture_processing_id, previous_operation_id)
        REFERENCES background_operations (lecture_processing_id, operation_id)
);

COMMENT ON TABLE app_users IS
    'Rakenduse kasutajad ja nende rakenduserollid';
COMMENT ON COLUMN app_users.user_id IS
    'Kasutaja tehniline identifikaator';
COMMENT ON COLUMN app_users.public_id IS
    'Avalikus API-s kasutatav UUID';
COMMENT ON COLUMN app_users.identity_provider IS
    'Autentimispakkuja püsiv kood';
COMMENT ON COLUMN app_users.external_subject IS
    'Autentimispakkuja stabiilne kasutajatunnus';
COMMENT ON COLUMN app_users.email IS
    'Kasutaja normaliseeritud e-posti aadress';
COMMENT ON COLUMN app_users.display_name IS
    'Kasutajale kuvatav nimi';
COMMENT ON COLUMN app_users.role_code IS
    'Rakenduseroll';
COMMENT ON COLUMN app_users.enabled IS
    '1 tähendab lubatud ja 0 keelatud kasutajat';

COMMENT ON TABLE submissions IS
    'Ühe kasutajategevusega esitatud Echo360 loengute grupp';
COMMENT ON COLUMN submissions.submission_id IS
    'Esitamise tehniline identifikaator';
COMMENT ON COLUMN submissions.public_id IS
    'Esitamise avalik UUID';
COMMENT ON COLUMN submissions.user_id IS
    'Esitamise loonud rakenduse kasutaja';
COMMENT ON COLUMN submissions.echo_public_url IS
    'Kasutaja sisestatud Echo360 avalik URL';
COMMENT ON COLUMN submissions.echo_public_section_id IS
    'Echo360 avaliku sektsiooni UUID';
COMMENT ON COLUMN submissions.echo_canonical_section_id IS
    'Echo360 kanoonilise sektsiooni UUID';
COMMENT ON COLUMN submissions.course_title IS
    'Echo360 kursuse nimi lahendamise hetkel';
COMMENT ON COLUMN submissions.resolver_manifest_path IS
    'Runtime-juure suhteline tee resolveri JSON-manifestini';

COMMENT ON TABLE lecture_processings IS
    'Ühe valitud Echo360 loengu töötluskontekst';
COMMENT ON COLUMN lecture_processings.lecture_processing_id IS
    'Loengutöötluse tehniline identifikaator';
COMMENT ON COLUMN lecture_processings.public_id IS
    'Avaliku read-only jagamislingi UUID; NULL keelab jagamise';
COMMENT ON COLUMN lecture_processings.submission_id IS
    'Esitamine, mille koosseisu loeng kuulub';
COMMENT ON COLUMN lecture_processings.echo_lesson_id IS
    'Echo360 loengu UUID';
COMMENT ON COLUMN lecture_processings.lecture_title IS
    'Loengu nimi lahendamise hetkel';
COMMENT ON COLUMN lecture_processings.lecture_start_at IS
    'Echo360 loengu algusaeg UTC-s';
COMMENT ON COLUMN lecture_processings.duration_seconds IS
    'Loengusalvestise kestus sekundites';
COMMENT ON COLUMN lecture_processings.recording_status IS
    'Echo360 salvestise olek lahendamise hetkel';

COMMENT ON TABLE uploads IS
    'Kasutaja üleslaaditud sisendfailide metaandmed';
COMMENT ON COLUMN uploads.upload_id IS
    'Üleslaadimise tehniline identifikaator';
COMMENT ON COLUMN uploads.public_id IS
    'Üleslaadimise avalik UUID';
COMMENT ON COLUMN uploads.lecture_processing_id IS
    'Loengutöötlus, millega fail on seotud';
COMMENT ON COLUMN uploads.upload_type IS
    'Üleslaaditud faili liik';
COMMENT ON COLUMN uploads.original_filename IS
    'Kasutaja faili algne nimi';
COMMENT ON COLUMN uploads.stored_relative_path IS
    'Rakenduse input-juure suhteline salvestustee';
COMMENT ON COLUMN uploads.media_type IS
    'Faili MIME-tüüp';
COMMENT ON COLUMN uploads.size_bytes IS
    'Faili suurus baitides, kui see on teada';
COMMENT ON COLUMN uploads.sha256 IS
    'Faili SHA-256 kontrollsumma, kui see on arvutatud';

COMMENT ON TABLE background_operations IS
    'Rakenduse taustatoimingute seosed ORDS-i töödega';
COMMENT ON COLUMN background_operations.operation_id IS
    'Taustatoimingu tehniline identifikaator';
COMMENT ON COLUMN background_operations.public_id IS
    'Taustatoimingu avalik UUID';
COMMENT ON COLUMN background_operations.lecture_processing_id IS
    'Loengutöötlus, mille jaoks toiming loodi';
COMMENT ON COLUMN background_operations.previous_operation_id IS
    'Sama loengu eelmine toiming';
COMMENT ON COLUMN background_operations.operation_type IS
    'Rakenduse toimingu liik';
COMMENT ON COLUMN background_operations.attempt_number IS
    'Loengu ja toiminguliigi katse number';
COMMENT ON COLUMN background_operations.idempotency_key IS
    'ORDS-ile saadetud korduskindluse võti';
COMMENT ON COLUMN background_operations.ords_job_id IS
    'ORDS-i tagastatud keskne job_id';
COMMENT ON COLUMN background_operations.registration_error_code IS
    'ORDS-i registreerimisvea kood';
COMMENT ON COLUMN background_operations.registration_error_message IS
    'ORDS-i registreerimisvea saladusteta kirjeldus';
COMMENT ON COLUMN background_operations.ords_registered_at IS
    'ORDS-i job_id sidumise aeg UTC-s';
COMMENT ON COLUMN background_operations.local_started_at IS
    'Rakenduse adapteri tegelik algusaeg';
COMMENT ON COLUMN background_operations.local_completed_at IS
    'Rakenduse adapteri tegelik lõppaeg';
COMMENT ON COLUMN background_operations.local_outcome IS
    'Rakenduse adapteri kohalik tulemus';
COMMENT ON COLUMN background_operations.local_error_code IS
    'Rakenduse sisemise vea kood';
COMMENT ON COLUMN background_operations.local_error_message IS
    'Rakenduse sisemise vea saladusteta kirjeldus';

