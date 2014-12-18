SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'LATIN1';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: projects; Type: TABLE; Schema: public; Owner: optima; Tablespace:
--

CREATE TABLE projects (
    id integer NOT NULL,
    name character varying(60),
    user_id integer,
    datastart integer,
    dataend integer,
    econ_dataend integer,
    programs json,
    populations json
);


ALTER TABLE public.projects OWNER TO optima;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: optima
--

CREATE SEQUENCE projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO optima;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optima
--

ALTER SEQUENCE projects_id_seq OWNED BY projects.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: optima; Tablespace:
--

CREATE TABLE users (
    id integer NOT NULL,
    name character varying(60),
    email character varying(200),
    password character varying(200)
);


ALTER TABLE public.users OWNER TO optima;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: optima
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO optima;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: optima
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: working_projects; Type: TABLE; Schema: public; Owner: optima; Tablespace:
--

CREATE TABLE working_projects (
    id integer NOT NULL,
    is_calibrating boolean,
    model json
);


ALTER TABLE public.working_projects OWNER TO optima;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: optima
--

ALTER TABLE ONLY projects ALTER COLUMN id SET DEFAULT nextval('projects_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: optima
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Name: projects_pkey; Type: CONSTRAINT; Schema: public; Owner: optima; Tablespace:
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: optima; Tablespace:
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: working_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: optima; Tablespace:
--

ALTER TABLE ONLY working_projects
    ADD CONSTRAINT working_projects_pkey PRIMARY KEY (id);


--
-- Name: projects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optima
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: working_projects_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: optima
--

ALTER TABLE ONLY working_projects
    ADD CONSTRAINT working_projects_id_fkey FOREIGN KEY (id) REFERENCES projects(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
