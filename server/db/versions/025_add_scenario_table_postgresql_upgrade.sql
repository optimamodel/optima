CREATE TABLE scenario (
    id UUID DEFAULT uuid_generate_v1mc() NOT NULL,
    project_id UUID,
    name VARCHAR,
    scenario_type VARCHAR,
    active BOOLEAN,
    progset_id UUID,
    parset_id UUID,
    blob JSON,

    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES projects (id),
    FOREIGN KEY(progset_id) REFERENCES progsets (id),
    FOREIGN KEY(parset_id) REFERENCES parsets (id)
);
