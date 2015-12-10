CREATE TABLE progsets (
    id UUID DEFAULT uuid_generate_v1mc() NOT NULL,
    project_id UUID,
    name VARCHAR,
    created TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE TABLE programs (
    id UUID DEFAULT uuid_generate_v1mc() NOT NULL,
    progset_id UUID,
    category VARCHAR,
    name VARCHAR,
    short_name VARCHAR,
    pars BYTEA,
    active BOOLEAN,
    created TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(progset_id) REFERENCES progsets (id)
);