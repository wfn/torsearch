SET statement_timeout = 0;
SET client_encoding = 'LATIN1';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET search_path = public, pg_catalog;
SET default_tablespace = '';
SET default_with_oids = false;

--
-- Name: consensus; Type: TABLE; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE TABLE consensus (
    valid_after timestamp without time zone NOT NULL,
    fresh_until timestamp without time zone,
    valid_until timestamp without time zone
);


ALTER TABLE public.consensus OWNER TO tsusr;

--
-- Name: descriptor; Type: TABLE; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE TABLE descriptor (
    descriptor character varying(40) NOT NULL,
    fingerprint character varying(40),
    nickname character varying(19),
    published timestamp without time zone,
    address character varying(15),
    or_port integer,
    dir_port integer,
    platform character varying(256),
    uptime bigint,
    contact bytea,
    exit_policy character varying,
    average_bandwidth bigint,
    burst_bandwidth bigint,
    observed_bandwidth bigint,
    hibernating boolean DEFAULT false,
    extra_info_digest character varying(40),
    is_bridge boolean DEFAULT false,
    id integer NOT NULL
);


ALTER TABLE public.descriptor OWNER TO tsusr;

--
-- Name: descriptor_id_seq; Type: SEQUENCE; Schema: public; Owner: tsusr
--

CREATE SEQUENCE descriptor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.descriptor_id_seq OWNER TO tsusr;

--
-- Name: descriptor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tsusr
--

ALTER SEQUENCE descriptor_id_seq OWNED BY descriptor.id;


--
-- Name: fingerprint; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE fingerprint (
    fp12 character(12) NOT NULL,
    fingerprint character(40) NOT NULL,
    digest character(40) NOT NULL,
    nickname character varying(19) NOT NULL,
    address character varying(15) NOT NULL,
    first_va timestamp without time zone NOT NULL,
    last_va timestamp without time zone NOT NULL,
    sid integer NOT NULL
);


ALTER TABLE public.fingerprint OWNER TO postgres;

--
-- Name: statusentry; Type: TABLE; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE TABLE statusentry (
    validafter timestamp without time zone NOT NULL,
    nickname character varying(19),
    fingerprint character varying(40) NOT NULL,
    published timestamp without time zone,
    descriptor character varying(40),
    address character varying(15),
    or_port integer,
    dir_port integer,
    version_line character varying(96),
    digest character varying(40) NOT NULL,
    bandwidth bigint,
    measured bigint,
    is_unmeasured boolean,
    "isAuthority" boolean,
    "isBadExit" boolean,
    "isBadDirectory" boolean,
    "isExit" boolean,
    "isFast" boolean,
    "isGuard" boolean,
    "isHSDir" boolean,
    "isNamed" boolean,
    "isStable" boolean,
    "isRunning" boolean,
    "isUnnamed" boolean,
    "isValid" boolean,
    "isV2Dir" boolean,
    "isV3Dir" boolean,
    id integer NOT NULL
);


ALTER TABLE public.statusentry OWNER TO tsusr;

--
-- Name: statusentry_id_seq; Type: SEQUENCE; Schema: public; Owner: tsusr
--

CREATE SEQUENCE statusentry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.statusentry_id_seq OWNER TO tsusr;

--
-- Name: statusentry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tsusr
--

ALTER SEQUENCE statusentry_id_seq OWNED BY statusentry.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: tsusr
--

ALTER TABLE ONLY descriptor ALTER COLUMN id SET DEFAULT nextval('descriptor_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: tsusr
--

ALTER TABLE ONLY statusentry ALTER COLUMN id SET DEFAULT nextval('statusentry_id_seq'::regclass);


--
-- Name: consensus_pkey; Type: CONSTRAINT; Schema: public; Owner: tsusr; Tablespace: 
--

ALTER TABLE ONLY consensus
    ADD CONSTRAINT consensus_pkey PRIMARY KEY (valid_after);


--
-- Name: descriptor_pkey; Type: CONSTRAINT; Schema: public; Owner: tsusr; Tablespace: 
--

ALTER TABLE ONLY descriptor
    ADD CONSTRAINT descriptor_pkey PRIMARY KEY (id);


--
-- Name: fingerprint_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY fingerprint
    ADD CONSTRAINT fingerprint_pkey PRIMARY KEY (fp12);


--
-- Name: statusentry_pkey; Type: CONSTRAINT; Schema: public; Owner: tsusr; Tablespace: 
--

ALTER TABLE ONLY statusentry
    ADD CONSTRAINT statusentry_pkey PRIMARY KEY (id);


--
-- Name: descriptor_lower_idx; Type: INDEX; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE INDEX descriptor_lower_idx ON descriptor USING btree (lower((nickname)::text));


--
-- Name: descriptor_substr_idx; Type: INDEX; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE INDEX descriptor_substr_idx ON descriptor USING btree (substr((fingerprint)::text, 0, 20));


--
-- Name: fingerprint_address_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fingerprint_address_idx ON fingerprint USING btree (address);


--
-- Name: fingerprint_last_va_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fingerprint_last_va_idx ON fingerprint USING btree (last_va);


--
-- Name: fingerprint_lower_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX fingerprint_lower_idx ON fingerprint USING btree (lower((nickname)::text));


--
-- Name: statusentry_substr_validafter_idx; Type: INDEX; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE UNIQUE INDEX statusentry_substr_validafter_idx ON statusentry USING btree (substr((fingerprint)::text, 0, 12), validafter DESC);


--
-- Name: statusentry_validafter_idx; Type: INDEX; Schema: public; Owner: tsusr; Tablespace: 
--

CREATE INDEX statusentry_validafter_idx ON statusentry USING btree (validafter);

