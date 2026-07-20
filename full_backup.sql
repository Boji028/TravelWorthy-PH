--
-- PostgreSQL database dump
--

\restrict 0LUeGtFg4IMDlrxYU2IxeZco5KeKoDJ0MbJaq3OTYfCqA4aCr0gbcqdfZTEIIAY

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agents (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    notes character varying(255),
    is_active boolean,
    created_at timestamp without time zone,
    is_visa_agent boolean NOT NULL
);


ALTER TABLE public.agents OWNER TO postgres;

--
-- Name: agents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.agents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agents_id_seq OWNER TO postgres;

--
-- Name: agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.agents_id_seq OWNED BY public.agents.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: blog_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blog_posts (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    author character varying(100) NOT NULL,
    category character varying(100),
    short_description text,
    content text NOT NULL,
    featured_image character varying(300),
    featured_image_size_kb double precision,
    featured_image_uploaded_at timestamp without time zone,
    is_published boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.blog_posts OWNER TO postgres;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.blog_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.blog_posts_id_seq OWNER TO postgres;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.blog_posts_id_seq OWNED BY public.blog_posts.id;


--
-- Name: contact_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contact_messages (
    id integer NOT NULL,
    user_id integer,
    name character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    subject character varying(200) NOT NULL,
    message text NOT NULL,
    is_read boolean,
    created_at timestamp without time zone,
    admin_response text,
    responded_at timestamp without time zone
);


ALTER TABLE public.contact_messages OWNER TO postgres;

--
-- Name: contact_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contact_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contact_messages_id_seq OWNER TO postgres;

--
-- Name: contact_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contact_messages_id_seq OWNED BY public.contact_messages.id;


--
-- Name: continents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.continents (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    flag_emoji character varying(10),
    image character varying(300),
    image_size_kb double precision,
    image_uploaded_at timestamp without time zone,
    description text,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.continents OWNER TO postgres;

--
-- Name: continents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.continents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.continents_id_seq OWNER TO postgres;

--
-- Name: continents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.continents_id_seq OWNED BY public.continents.id;


--
-- Name: countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.countries (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    flag_emoji character varying(10),
    image character varying(300),
    image_size_kb double precision,
    image_uploaded_at timestamp without time zone,
    description text,
    is_active boolean,
    created_at timestamp without time zone,
    continent_id integer
);


ALTER TABLE public.countries OWNER TO postgres;

--
-- Name: countries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.countries_id_seq OWNER TO postgres;

--
-- Name: countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.countries_id_seq OWNED BY public.countries.id;


--
-- Name: email_verification_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_verification_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(128) NOT NULL,
    email character varying(150) NOT NULL,
    created_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL,
    verified_at timestamp without time zone,
    is_used boolean
);


ALTER TABLE public.email_verification_tokens OWNER TO postgres;

--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_verification_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_verification_tokens_id_seq OWNER TO postgres;

--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_verification_tokens_id_seq OWNED BY public.email_verification_tokens.id;


--
-- Name: inquiries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inquiries (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    contact_number character varying(20) NOT NULL,
    destination character varying(200) NOT NULL,
    travel_date_from date NOT NULL,
    travel_date_to date NOT NULL,
    num_adults integer NOT NULL,
    num_children integer NOT NULL,
    num_infants integer NOT NULL,
    special_requests text,
    status character varying(20) NOT NULL,
    inquiry_type character varying(20),
    created_at timestamp without time zone,
    admin_response text,
    responded_at timestamp without time zone,
    package_id integer,
    reference_number character varying(20) NOT NULL,
    user_id integer,
    last_exported_at timestamp without time zone,
    confirmation_email_failed boolean DEFAULT false NOT NULL
);


ALTER TABLE public.inquiries OWNER TO postgres;

--
-- Name: inquiries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inquiries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inquiries_id_seq OWNER TO postgres;

--
-- Name: inquiries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inquiries_id_seq OWNED BY public.inquiries.id;


--
-- Name: inquiry_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inquiry_notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    inquiry_id integer,
    message character varying(255) NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamp without time zone,
    link_url character varying(255)
);


ALTER TABLE public.inquiry_notifications OWNER TO postgres;

--
-- Name: inquiry_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inquiry_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inquiry_notifications_id_seq OWNER TO postgres;

--
-- Name: inquiry_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inquiry_notifications_id_seq OWNED BY public.inquiry_notifications.id;


--
-- Name: package_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_images (
    id integer NOT NULL,
    package_id integer NOT NULL,
    path character varying(300) NOT NULL,
    "order" integer,
    uploaded_at timestamp without time zone
);


ALTER TABLE public.package_images OWNER TO postgres;

--
-- Name: package_images_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_images_id_seq OWNER TO postgres;

--
-- Name: package_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_images_id_seq OWNED BY public.package_images.id;


--
-- Name: package_reviews; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_reviews (
    id integer NOT NULL,
    package_id integer NOT NULL,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    message text NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.package_reviews OWNER TO postgres;

--
-- Name: package_reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_reviews_id_seq OWNER TO postgres;

--
-- Name: package_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_reviews_id_seq OWNED BY public.package_reviews.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(128) NOT NULL,
    created_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL,
    used_at timestamp without time zone,
    is_used boolean
);


ALTER TABLE public.password_reset_tokens OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: site_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.site_settings (
    id integer NOT NULL,
    hero_image character varying(300),
    hero_image_size_kb double precision,
    hero_image_uploaded_at timestamp without time zone,
    testimonial_image character varying(300),
    testimonial_image_size_kb double precision,
    testimonial_image_uploaded_at timestamp without time zone,
    cta_image character varying(300),
    cta_image_size_kb double precision,
    cta_image_uploaded_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.site_settings OWNER TO postgres;

--
-- Name: site_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.site_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.site_settings_id_seq OWNER TO postgres;

--
-- Name: site_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.site_settings_id_seq OWNED BY public.site_settings.id;


--
-- Name: testimonial_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.testimonial_images (
    id integer NOT NULL,
    testimonial_id integer NOT NULL,
    path character varying(500) NOT NULL,
    "order" integer,
    created_at timestamp without time zone
);


ALTER TABLE public.testimonial_images OWNER TO postgres;

--
-- Name: testimonial_images_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.testimonial_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.testimonial_images_id_seq OWNER TO postgres;

--
-- Name: testimonial_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.testimonial_images_id_seq OWNED BY public.testimonial_images.id;


--
-- Name: testimonials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.testimonials (
    id integer NOT NULL,
    user_id integer NOT NULL,
    message text NOT NULL,
    rating integer NOT NULL,
    image character varying(300),
    image_size_kb double precision,
    image_uploaded_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.testimonials OWNER TO postgres;

--
-- Name: testimonials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.testimonials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.testimonials_id_seq OWNER TO postgres;

--
-- Name: testimonials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.testimonials_id_seq OWNED BY public.testimonials.id;


--
-- Name: tour_packages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tour_packages (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    destination character varying(150) NOT NULL,
    country_id integer,
    duration_days integer NOT NULL,
    price numeric(12,2) NOT NULL,
    currency character varying(10),
    image character varying(300),
    image_size_kb double precision,
    image_uploaded_at timestamp without time zone,
    inclusions text,
    exclusions text,
    is_active boolean,
    created_at timestamp without time zone,
    is_featured boolean,
    updated_at timestamp without time zone,
    amenities text,
    location_description text,
    latitude double precision,
    longitude double precision,
    flier_image character varying(300),
    flier_image_size_kb double precision,
    flier_image_uploaded_at timestamp without time zone,
    package_type character varying(20) NOT NULL,
    assigned_agent_id integer
);


ALTER TABLE public.tour_packages OWNER TO postgres;

--
-- Name: tour_packages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tour_packages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tour_packages_id_seq OWNER TO postgres;

--
-- Name: tour_packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tour_packages_id_seq OWNED BY public.tour_packages.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    password character varying(200),
    phone character varying(20),
    is_admin boolean,
    created_at timestamp without time zone,
    email_verified boolean DEFAULT false,
    email_verified_at timestamp without time zone,
    oauth_provider character varying(20),
    oauth_id character varying(255),
    session_token character varying(32)
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: visa_countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.visa_countries (
    id integer NOT NULL,
    country_name character varying(100) NOT NULL,
    flag_emoji character varying(10),
    requirements_pdf character varying(300),
    price double precision,
    is_active boolean,
    created_at timestamp without time zone,
    region character varying(100),
    visa_type character varying(50),
    processing_time character varying(50),
    stay_validity character varying(50),
    documents_count integer
);


ALTER TABLE public.visa_countries OWNER TO postgres;

--
-- Name: visa_countries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.visa_countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.visa_countries_id_seq OWNER TO postgres;

--
-- Name: visa_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.visa_countries_id_seq OWNED BY public.visa_countries.id;


--
-- Name: agents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agents ALTER COLUMN id SET DEFAULT nextval('public.agents_id_seq'::regclass);


--
-- Name: blog_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blog_posts ALTER COLUMN id SET DEFAULT nextval('public.blog_posts_id_seq'::regclass);


--
-- Name: contact_messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contact_messages ALTER COLUMN id SET DEFAULT nextval('public.contact_messages_id_seq'::regclass);


--
-- Name: continents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.continents ALTER COLUMN id SET DEFAULT nextval('public.continents_id_seq'::regclass);


--
-- Name: countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries ALTER COLUMN id SET DEFAULT nextval('public.countries_id_seq'::regclass);


--
-- Name: email_verification_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens ALTER COLUMN id SET DEFAULT nextval('public.email_verification_tokens_id_seq'::regclass);


--
-- Name: inquiries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiries ALTER COLUMN id SET DEFAULT nextval('public.inquiries_id_seq'::regclass);


--
-- Name: inquiry_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiry_notifications ALTER COLUMN id SET DEFAULT nextval('public.inquiry_notifications_id_seq'::regclass);


--
-- Name: package_images id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_images ALTER COLUMN id SET DEFAULT nextval('public.package_images_id_seq'::regclass);


--
-- Name: package_reviews id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_reviews ALTER COLUMN id SET DEFAULT nextval('public.package_reviews_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: site_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site_settings ALTER COLUMN id SET DEFAULT nextval('public.site_settings_id_seq'::regclass);


--
-- Name: testimonial_images id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonial_images ALTER COLUMN id SET DEFAULT nextval('public.testimonial_images_id_seq'::regclass);


--
-- Name: testimonials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonials ALTER COLUMN id SET DEFAULT nextval('public.testimonials_id_seq'::regclass);


--
-- Name: tour_packages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages ALTER COLUMN id SET DEFAULT nextval('public.tour_packages_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: visa_countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visa_countries ALTER COLUMN id SET DEFAULT nextval('public.visa_countries_id_seq'::regclass);


--
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agents (id, name, email, notes, is_active, created_at, is_visa_agent) FROM stdin;
1	Boji	claude6.afk@gmail.com	Newcoast Boracay	t	2026-06-28 14:27:38.475625	f
3	bojis	10claudeuser@gmail.com	\N	t	2026-06-28 15:19:49.931813	t
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
a1c5e9f3b7d2
\.


--
-- Data for Name: blog_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.blog_posts (id, title, author, category, short_description, content, featured_image, featured_image_size_kb, featured_image_uploaded_at, is_published, created_at, updated_at) FROM stdin;
2	test	Admin	test		test	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1780908707/travelworthyph/blog/aoeigfcydzmznx8ffrni.jpg	1594.52	2026-06-08 16:51:48.375157	t	2026-06-08 16:51:48.380098	2026-06-08 16:51:48.404345
\.


--
-- Data for Name: contact_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contact_messages (id, user_id, name, email, subject, message, is_read, created_at, admin_response, responded_at) FROM stdin;
20	13	bojis2113	castillo.markenzo.m.c210208@gmail.com	test	test	f	2026-07-01 10:57:36.973706	\N	\N
21	13	bojis2113	castillo.markenzo.m.c210208@gmail.com	test	subukeee	f	2026-07-01 11:07:44.496804	\N	\N
22	\N	Mark Enzo Castillo	castillo.markenzo.m.c210208@gmail.com	test test	test	f	2026-07-17 11:10:22.285881	\N	\N
23	\N	Mark Enzo Castillo	castillo.markenzo.m.c210208@gmail.com	test test	testtttttttt	t	2026-07-17 11:42:54.522993	tryyy response	2026-07-17 11:46:16.064285
\.


--
-- Data for Name: continents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.continents (id, name, flag_emoji, image, image_size_kb, image_uploaded_at, description, is_active, created_at) FROM stdin;
1	Asia	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782011408/travelworthyph/continent/lhdscwc6a2gj8ih0lcxf.jpg	1711.23	2026-06-21 11:10:09.655057		t	2026-06-03 14:01:06.138067
2	Europe	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782011424/travelworthyph/continent/zkckh7if87arjxji4lbg.jpg	536.5	2026-06-21 11:10:24.169107		t	2026-06-03 14:01:11.717994
3	North America	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782011437/travelworthyph/continent/kxpcdmb1vr5dgnx1o4e1.jpg	1433.38	2026-06-21 11:10:39.084017		t	2026-06-03 14:01:17.130794
4	Oceania	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782011454/travelworthyph/continent/m7bjsabmn24s5sujihlu.jpg	406.49	2026-06-21 11:10:55.473045		t	2026-06-03 14:01:23.828914
\.


--
-- Data for Name: countries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.countries (id, name, flag_emoji, image, image_size_kb, image_uploaded_at, description, is_active, created_at, continent_id) FROM stdin;
1	Philippines	PH		\N	\N		t	2026-06-03 14:01:29.218639	1
2	China	CN		\N	\N		t	2026-06-03 14:01:40.874443	1
4	Taiwan	TW		\N	\N		t	2026-06-03 14:02:06.515069	1
6	Spain	SP		\N	\N		t	2026-06-03 14:02:45.335461	2
7	Hawaii	HW		\N	\N		t	2026-06-03 14:02:55.25014	3
8	Australia	AU		\N	\N		t	2026-06-03 14:03:03.84452	4
3	South Korea	KR	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782292617/travelworthyph/country/g78xjijjcmw3nm91p5zk.png	5.91	2026-06-24 17:16:59.11925		t	2026-06-03 14:01:50.237776	1
9	New Zealand	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561907/travelworthyph/country/ei9uwe9ktmbb5pttu7lc.jpg	6.06	2026-07-09 09:51:48.019076		t	2026-07-09 09:51:48.020377	4
10	Palau	🌏	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567620/travelworthyph/country/xndo1lmiuiy7r07rm4kc.jpg	2.16	2026-07-09 11:27:00.994315		t	2026-07-09 11:27:00.996926	4
\.


--
-- Data for Name: email_verification_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_verification_tokens (id, user_id, token, email, created_at, expires_at, verified_at, is_used) FROM stdin;
\.


--
-- Data for Name: inquiries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inquiries (id, name, email, contact_number, destination, travel_date_from, travel_date_to, num_adults, num_children, num_infants, special_requests, status, inquiry_type, created_at, admin_response, responded_at, package_id, reference_number, user_id, last_exported_at, confirmation_email_failed) FROM stdin;
23	bojina	castillo.markenzo.m.c210208@gmail.com	09064842489	test	2026-06-22	2026-06-24	1	0	0		confirmed	general	2026-06-16 15:28:33.513195	\N	\N	9	INQ-C61C8	\N	2026-07-09 17:09:04.618509	f
24	bojiss	castillo.markenzo.m.c210208@gmail.com	09064842489	Japan	2026-06-22	2026-06-24	1	0	0	[FOR VISA] 	confirmed	general	2026-06-16 15:35:04.133722	\N	\N	\N	INQ-C32DA	\N	2026-07-09 17:09:04.618509	f
26	Caiga	castillo.markenzo.m.c210208@gmail.com	09064842489	Japan	2026-06-30	2026-07-02	1	0	0	[FOR VISA] 	contacted	general	2026-06-19 16:28:24.538629	\N	\N	\N	INQ-A5176F	\N	2026-07-09 17:09:04.618509	f
25	 B. Caiga	castillo.markenzo.m.c210208@gmail.com	09064842489	test	2026-06-21	2026-06-23	1	0	0	test	confirmed	general	2026-06-19 16:26:58.172239	\N	\N	9	INQ-2A3535	\N	2026-07-09 17:09:04.618509	f
46	bojis2	castillo.markenzo.m.c210208@gmail.com	09064842489	test	2026-07-01	2026-07-02	1	0	0	test	new	general	2026-06-30 17:29:13.340253	\N	\N	8	INQ-128DDA	13	2026-07-09 17:09:04.618509	f
79	bojis21	castillo.markenzo.m.c210208@gmail.com	09064842489	SOUTH KOREA	2026-07-08	2026-07-10	1	0	0	subok	confirmed	general	2026-06-30 17:57:47.319547	\N	\N	10	INQ-C3E029	13	2026-07-09 17:09:04.618509	f
80	bowji	castillo.markenzo.m.c210208@gmail.com	09064842489	Japan	2026-07-01	2026-07-10	1	0	0	[FOR VISA] 	new	general	2026-06-30 18:16:15.811563	\N	\N	\N	INQ-7083E6	13	2026-07-09 17:09:04.618509	f
81	bojis211	castillo.markenzo.m.c210208@gmail.com	09064842489	test	2026-07-01	2026-07-03	1	0	0	test	new	general	2026-06-30 18:29:56.355527	\N	\N	9	INQ-14A170	13	2026-07-09 17:09:04.618509	f
82	Abigail Kristine Paola B. Caiga	castillo.markenzo.m.c210208@gmail.com	09064842489	South Korea	2026-07-01	2026-07-10	1	0	0	[FOR VISA] 	new	general	2026-06-30 18:31:12.103538	\N	\N	\N	INQ-12610F	13	2026-07-09 17:09:04.618509	f
114	enzo	castillo.markenzo.m.c210208@gmail.com	09064842489	United State	2026-07-15	2026-07-24	1	0	0	[FOR VISA] testtt	confirmed	general	2026-07-01 10:12:26.20538	\N	\N	\N	INQ-2C776B	13	2026-07-09 17:36:43.855097	f
115	enzo	castillo.markenzo.m.c210208@gmail.com	09064842489	Japan	2026-07-02	2026-07-18	1	0	0	[FOR VISA] test	confirmed	general	2026-07-01 10:23:10.631962	\N	\N	\N	INQ-27967E	13	2026-07-09 17:36:43.855097	f
116	enzo	castillo.markenzo.m.c210208@gmail.com	09064842489	United State	2026-07-22	2026-07-28	1	0	0	[FOR VISA] 	confirmed	general	2026-07-01 10:27:39.337521	\N	\N	\N	INQ-72AC19	13	2026-07-09 17:36:43.855097	f
117	bojis2111	castillo.markenzo.m.c210208@gmail.com	09064842489	Palawan	2026-07-14	2026-07-17	1	0	0	testt	confirmed	general	2026-07-01 10:39:07.145563	\N	\N	\N	INQ-5F50EF	13	2026-07-09 17:36:43.855097	f
178	Boji Magnaye	castillo.markenzo.m.c210208@gmail.com	09064842489	Perth, Australia	2026-07-29	2026-07-29	11	0	0		new	general	2026-07-17 09:32:34.659956	\N	\N	20	INQ-2E2C7E	\N	\N	f
179	jake caiser	castillo.markenzo.m.c210208@gmail.com	09064842489	Palau	2026-07-28	2026-07-31	1	0	0		new	general	2026-07-17 09:52:15.952258	\N	\N	18	INQ-83AF5E	\N	\N	f
\.


--
-- Data for Name: inquiry_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inquiry_notifications (id, user_id, inquiry_id, message, is_read, created_at, link_url) FROM stdin;
29	13	46	We received your inquiry about test. We'll be in touch soon!	t	2026-06-30 17:29:13.353645	\N
30	11	46	New inquiry from bojis2 — test	t	2026-06-30 17:29:13.355713	\N
62	13	79	We received your inquiry about SOUTH KOREA. We'll be in touch soon!	t	2026-06-30 17:57:47.335929	\N
71	13	82	We received your inquiry about South Korea. We'll be in touch soon!	t	2026-06-30 18:31:12.106669	\N
69	13	81	We received your inquiry about test. We'll be in touch soon!	t	2026-06-30 18:29:56.364297	\N
66	13	79	Your inquiry to SOUTH KOREA is now confirmed.	t	2026-06-30 18:00:21.295943	\N
65	13	79	Your inquiry to SOUTH KOREA is now closed.	t	2026-06-30 18:00:14.654951	\N
67	13	80	We received your inquiry about Japan. We'll be in touch soon!	t	2026-06-30 18:16:15.833567	\N
64	13	79	Your inquiry to SOUTH KOREA is now contacted.	t	2026-06-30 17:59:56.851082	\N
72	11	82	New inquiry from Abigail Kristine Paola B. Caiga — South Korea	t	2026-06-30 18:31:12.108021	\N
70	11	81	New inquiry from bojis211 — test	t	2026-06-30 18:29:56.368472	\N
68	11	80	New inquiry from bowji — Japan	t	2026-06-30 18:16:15.835768	\N
63	11	79	New inquiry from bojis21 — SOUTH KOREA	t	2026-06-30 17:57:47.339609	\N
102	13	114	We received your inquiry about United State. We'll be in touch soon!	t	2026-07-01 10:12:26.214596	\N
103	11	114	New inquiry from enzo — United State	t	2026-07-01 10:12:26.218078	\N
105	13	114	Your inquiry to United State is now confirmed.	t	2026-07-01 10:14:32.27061	\N
104	13	114	Your inquiry to United State is now contacted.	t	2026-07-01 10:14:09.38115	\N
107	11	115	New inquiry from enzo — Japan	t	2026-07-01 10:23:10.649611	\N
113	11	117	New inquiry from bojis2111 — Palawan	t	2026-07-01 10:39:07.157965	\N
110	11	116	New inquiry from enzo — United State	t	2026-07-01 10:27:39.354712	\N
114	13	117	Your inquiry to Palawan is now confirmed.	t	2026-07-01 10:40:02.560959	\N
112	13	117	We received your inquiry about Palawan. We'll be in touch soon!	t	2026-07-01 10:39:07.153184	\N
111	13	116	Your inquiry to United State is now confirmed.	t	2026-07-01 10:28:28.574356	\N
109	13	116	We received your inquiry about United State. We'll be in touch soon!	t	2026-07-01 10:27:39.352873	\N
108	13	115	Your inquiry to Japan is now confirmed.	t	2026-07-01 10:24:01.687299	\N
106	13	115	We received your inquiry about Japan. We'll be in touch soon!	t	2026-07-01 10:23:10.647509	\N
118	11	\N	2 inquiries will be auto-deleted in the next 7 days. Download them from Inquiries before they're removed.	t	2026-07-09 17:36:15.352537	\N
119	12	\N	New visa info added: China — check it out!	f	2026-07-12 11:31:06.313862	/packages/visa
121	12	\N	New visa info added: Dubai — check it out!	f	2026-07-12 11:39:36.09308	/packages/visa
123	12	\N	New visa info added: Canada — check it out!	f	2026-07-12 11:42:32.919586	/packages/visa
125	12	\N	New visa info added: Australia — check it out!	f	2026-07-12 11:47:46.253944	/packages/visa
127	12	\N	New visa info added: United Kingdom — check it out!	f	2026-07-12 11:51:58.045825	/packages/visa
129	12	\N	New visa info added: Switzerland — check it out!	f	2026-07-12 12:13:10.876891	/packages/visa
130	13	\N	New visa info added: Switzerland — check it out!	t	2026-07-12 12:13:10.876899	/packages/visa
128	13	\N	New visa info added: United Kingdom — check it out!	t	2026-07-12 11:51:58.045834	/packages/visa
126	13	\N	New visa info added: Australia — check it out!	t	2026-07-12 11:47:46.253957	/packages/visa
124	13	\N	New visa info added: Canada — check it out!	t	2026-07-12 11:42:32.919595	/packages/visa
122	13	\N	New visa info added: Dubai — check it out!	t	2026-07-12 11:39:36.093089	/packages/visa
120	13	\N	New visa info added: China — check it out!	t	2026-07-12 11:31:06.313874	/packages/visa
131	11	178	New inquiry from Boji Magnaye — Perth, Australia	f	2026-07-17 09:32:34.725383	\N
132	11	179	New inquiry from jake caiser — Palau	f	2026-07-17 09:52:15.9924	\N
\.


--
-- Data for Name: package_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_images (id, package_id, path, "order", uploaded_at) FROM stdin;
1	8	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781064725/travelworthyph/package/yyfk6aoty6ryg3wxfjuy.jpg	0	2026-06-10 12:12:07.698402
2	8	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781066478/travelworthyph/package/mauyo3vs5ihb75gsjgds.png	1	2026-06-10 12:41:26.181803
3	8	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781066481/travelworthyph/package/onwzvmlsa3aerkdulqqu.png	1	2026-06-10 12:41:26.181809
4	9	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781257265/travelworthyph/package/x9bnx1h9r0ktel6rtdgg.jpg	0	2026-06-12 17:41:13.173358
5	9	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781257323/travelworthyph/package/gikcn0nfndqe8nrlunqo.jpg	1	2026-06-12 17:42:26.946845
6	9	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781257328/travelworthyph/package/imhdhdgteypnghcnsnvq.png	1	2026-06-12 17:42:26.946849
7	9	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781257344/travelworthyph/package/fy7mwadmrfxaufrnkohj.jpg	1	2026-06-12 17:42:26.94685
\.


--
-- Data for Name: package_reviews; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.package_reviews (id, package_id, user_id, rating, message, created_at) FROM stdin;
1	9	13	4	testing	2026-06-14 13:15:33.598118
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.password_reset_tokens (id, user_id, token, created_at, expires_at, used_at, is_used) FROM stdin;
1	13	JA6z2f9gZrFP5eLLTSHCNbrDWuvl2hOGdoHiRy1AoF8fchUsTmdc9hszFv4fVla6fdy5R7EdB2QDM0MGxo1LjQ	2026-07-07 12:30:46.711933	2026-07-07 13:30:46.709935	2026-07-07 12:32:47.756379	t
2	13	KIIR2T9skEzIZZPqhg4nHebh6N7pa-F2PpKOoksHq-iVpmPKANZc6UDW-wWOtolha9xSQ5UYXEJag2Vlip3fSw	2026-07-09 15:46:43.975594	2026-07-09 16:46:43.969879	2026-07-09 15:47:52.126399	t
3	13	cc9oQOpv8LUY5XuQZZDMqh_RVwk89l__Z55wAZ2RM8_wNFAwbqe4AYoLX2ZKEz6uDNFcYaQUWqOP9KG2kVpD3g	2026-07-12 13:20:05.058416	2026-07-12 14:20:05.054377	2026-07-12 13:21:04.347199	t
\.


--
-- Data for Name: site_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.site_settings (id, hero_image, hero_image_size_kb, hero_image_uploaded_at, testimonial_image, testimonial_image_size_kb, testimonial_image_uploaded_at, cta_image, cta_image_size_kb, cta_image_uploaded_at, updated_at) FROM stdin;
1	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782127350/travelworthyph/site_hero/ogypwajwkahrna6ibsr6.jpg	395.42	2026-06-22 19:22:31.538634	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1782127414/travelworthyph/site_testimonial/nxkju8ymlkp35sk9qwoh.jpg	241.8	2026-06-22 19:23:35.667478	\N	\N	\N	2026-06-28 09:01:15.334789
\.


--
-- Data for Name: testimonial_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.testimonial_images (id, testimonial_id, path, "order", created_at) FROM stdin;
5	8	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781503199/travelworthyph/review/hftcwd08uckw1yzlyczc.jpg	0	2026-06-15 13:59:59.879612
\.


--
-- Data for Name: testimonials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.testimonials (id, user_id, message, rating, image, image_size_kb, image_uploaded_at, created_at) FROM stdin;
8	11	test	1	\N	\N	\N	2026-06-15 13:59:59.87655
10	13	kkk	4	\N	\N	\N	2026-06-23 14:41:27.368145
\.


--
-- Data for Name: tour_packages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tour_packages (id, title, description, destination, country_id, duration_days, price, currency, image, image_size_kb, image_uploaded_at, inclusions, exclusions, is_active, created_at, is_featured, updated_at, amenities, location_description, latitude, longitude, flier_image, flier_image_size_kb, flier_image_uploaded_at, package_type, assigned_agent_id) FROM stdin;
9	Newcoast Boracay Package	test	BORACAY, PHILIPPINES	1	3	11.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781576706/travelworthyph/package/mfkx5vix4ctrflteb7xp.jpg	190.32	2026-06-16 10:25:08.015622		try	t	2026-06-12 12:30:37.645453	t	2026-07-01 09:23:34.762524			11.9686	121.9184	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781663053/travelworthyph/flier/o3i9vvepvkddeb5fdbgx.jpg	445.35	2026-06-17 10:24:15.650611	domestic	1
7	Boracay Astoria Hotel Package	test	BORACAY, PHILIPPINES	1	3	1111.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781411297/travelworthyph/package/eesowkc4uzbgnojmd8kq.jpg	203.48	2026-06-14 12:28:18.14732	1	1	t	2026-06-03 17:23:28.203018	t	2026-06-28 14:35:58.87605			\N	\N	\N	\N	\N	domestic	1
14	8 Days Hawaiian Highlights	.	Hawaii	7	8	265000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783562207/travelworthyph/package/djguteodaunwickmvumc.jpg	261.33	2026-07-09 09:56:48.333652			t	2026-07-09 09:56:49.878901	f	2026-07-09 09:56:49.885729			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783562208/travelworthyph/flier/mklgoq2gvn3ychjlfrve.jpg	377.96	2026-07-09 09:56:49.877484	international	\N
11	6 Days Melbourne Winter Highlights	..	Melbourne, Australia	8	6	155000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561369/travelworthyph/package/xorem7fjxuuptd90ngj8.jpg	209.75	2026-07-09 09:42:50.431002			t	2026-07-09 09:41:30.213303	f	2026-07-09 09:43:34.081919			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561288/travelworthyph/flier/yqxfkykwvydmgffmkdeq.jpg	298.26	2026-07-09 09:41:30.208285	international	\N
16	9 Days Melbourne & Sydney Discovery	..	Melbourne, Sydney, Australia	8	9	250000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567421/travelworthyph/package/ttap1zznqpm7vrh7xmkw.jpg	183.58	2026-07-09 11:23:41.990764			t	2026-07-09 11:23:43.572017	f	2026-07-09 11:23:43.594837			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567422/travelworthyph/flier/xbckdeos9oh1tlztyhxr.jpg	345.77	2026-07-09 11:23:43.570774	international	\N
12	7 Days Brisbane & Gold Coast Wonders	.	Brisbane, Australia	8	7	245000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561607/travelworthyph/package/j1ccd7e8txjojpyif2dm.jpg	287.61	2026-07-09 09:46:48.573424			t	2026-07-09 09:46:50.080978	f	2026-07-09 09:46:50.097923			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561608/travelworthyph/flier/bxwdd0e03uhyzqmu0rqx.jpg	395.32	2026-07-09 09:46:50.080243	international	\N
19	7 Days Brisbane & Gold Coast Wonders	..	Brisbane, Australia	8	7	240000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567814/travelworthyph/package/fcphghe0glwtshiufosi.jpg	281.99	2026-07-09 11:30:15.43284			t	2026-07-09 11:30:17.343494	f	2026-07-09 11:30:17.36785			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567815/travelworthyph/flier/fcaikeweldzxajp5hct9.jpg	410.45	2026-07-09 11:30:17.34232	international	\N
17	8 Days South New Zealand Hightlights	..	New Zealand	9	8	290000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567530/travelworthyph/package/zfsfljmfyoj52xasdzbc.jpg	327.6	2026-07-09 11:25:31.224037			t	2026-07-09 11:25:32.951256	f	2026-07-09 11:25:32.974253			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567531/travelworthyph/flier/srrrf7vgh3sgqcefqegk.jpg	409.12	2026-07-09 11:25:32.950394	international	\N
13	7 Days North Island New Zealand	..	New Zealand	9	7	190000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783565845/travelworthyph/package/s4owdupwhn1yfrhlizua.jpg	216.75	2026-07-09 10:57:26.203278			t	2026-07-09 09:53:20.985393	f	2026-07-09 10:57:26.204248			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783561999/travelworthyph/flier/wvxgnmwfqc4eywxznugl.jpg	322.94	2026-07-09 09:53:20.984221	international	\N
18	6 Days Palau Discovery	...	Palau	10	6	145000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567673/travelworthyph/package/gbtgys5dupjn8zyryw1n.jpg	313.95	2026-07-09 11:27:54.394796			t	2026-07-09 11:27:56.109323	f	2026-07-09 11:27:56.125231			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567674/travelworthyph/flier/cngn8b8z3h6jyelm2ahg.jpg	388.59	2026-07-09 11:27:56.107982	international	\N
15	7 Days Sydney Hightlights	..	Sydney, Australia	8	7	180000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567306/travelworthyph/package/uewvfsnix1hycjxj4y3c.jpg	267.5	2026-07-09 11:21:47.894057			t	2026-07-09 11:21:49.720825	f	2026-07-09 11:21:49.750603			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567308/travelworthyph/flier/bqq7mprksxueseut1n6n.jpg	368.81	2026-07-09 11:21:49.714853	international	\N
21	Autumn in Busan	..	Busan, South Korea	3	5	1088.00	USD	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783582542/travelworthyph/package/a7jy444ui4rzxnaimv07.jpg	369.27	2026-07-09 15:35:42.941063			t	2026-07-09 15:35:44.808971	f	2026-07-09 15:35:44.828171			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783582543/travelworthyph/flier/nyw8itnxcg0buq4s2wpn.jpg	489.21	2026-07-09 15:35:44.803447	international	\N
20	6 Days Perth Hightlights	..	Perth, Australia	8	6	185000.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567883/travelworthyph/package/bolzjazqfkvwnquziczu.jpg	233.78	2026-07-09 11:31:24.570883			t	2026-07-09 11:31:26.182497	f	2026-07-09 11:31:26.20115			\N	\N	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1783567884/travelworthyph/flier/g3xdli4q2xetw4eosrzv.jpg	266.36	2026-07-09 11:31:26.181415	international	\N
10	South Korea Winter Season Package	Test	SOUTH KOREA	3	3	111111.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781576982/travelworthyph/package/eizedtu7q9dq30yukt6y.jpg	373.75	2026-06-16 10:29:44.201782	11	11	t	2026-06-16 10:29:44.207182	f	2026-07-12 13:19:07.395732			\N	\N	\N	\N	\N	international	1
8	test	test	test	1	3	1.00	PHP	https://res.cloudinary.com/dbcjxuxhl/image/upload/v1781411856/travelworthyph/package/bto9mws0lecxzjd4ve6o.jpg	228.42	2026-06-14 12:37:36.682059			t	2026-06-08 13:17:55.021028	t	2026-07-12 13:23:52.882278	Hotel swimming pool\r\nDaily breakfast buffet\r\nFree WiFi at hotel\r\nAirport transfers included\r\nDirect beach access\r\nIsland hopping boat\r\nSnorkeling gear provided\r\nTour guide included\r\nWelcome drink on arrival\r\n24/7 Travel Worthy support		\N	\N	\N	\N	\N	domestic	1
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, name, email, password, phone, is_admin, created_at, email_verified, email_verified_at, oauth_provider, oauth_id, session_token) FROM stdin;
12	claude3	claude3.afk@gmail.com	scrypt:32768:8:1$V3fXN9G5JheusomN$fcde652e075e073efdcb5d5d50826b1f6791f2f0da2da92066283d4e334a826566f86ea66e96dc5656f69b431588e3757d1f401f3044b8a71b9594f5134e83a6	+639064842489	f	2026-06-08 14:19:33.869542	t	\N	\N	\N	\N
13	claudeTESTER	castillo.markenzo.m.c210208@gmail.com	scrypt:32768:8:1$1TxFEx8chiuert4u$e45c91b66d1d9f4d64f564c0097c774569b440c2e99787bfd95ebe50f68558c4a5ebe667e88f724be0c802d8cf857f236e5144a5d391a88b5ba2b4c478cfa32a	+639064842489	f	2026-06-09 15:03:31.39451	t	\N	google	117058977169441986598	\N
11	Admin	ragingsanford1@gmail.com	scrypt:32768:8:1$mbz2ZvDs5kPwT2vc$fecffa9c51aba3cda3eb639f03f457bb67110f1c981750fa464b4c26ead236f4a93fdff4216b3937501bcac67811da2f258d028321bff10d4086dbb5a5dd720e	\N	t	2026-06-08 13:16:34.690661	f	\N	\N	\N	8345eb334c10dcbd68e6c0c2f543fa27
\.


--
-- Data for Name: visa_countries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.visa_countries (id, country_name, flag_emoji, requirements_pdf, price, is_active, created_at, region, visa_type, processing_time, stay_validity, documents_count) FROM stdin;
4	China	CN	visa_8bd3ca47ce63423ebb715ce635778046.pdf	7000	t	2026-07-12 11:31:06.258063	Asia Pacific	Tourist	5-7 Days	30 Days	21
5	Dubai	AE	visa_2ccce7fd09b842c2a08c7ff494a4a62d.pdf	7500	t	2026-07-12 11:39:36.077937	Middle East	Tourist	5-7 Days	30 Days	21
7	Australia	AU	visa_d1ea8c90357f4c598f91b75888ced98a.pdf	14000	t	2026-07-12 11:47:46.247452	Oceania	Tourist	5-7 Days	30 Days	21
8	United Kingdom	GB	visa_15dba960c8d4491d9f3c8db08b38d190.pdf	14000	t	2026-07-12 11:51:58.038314	Europe	Tourist	5-7 Days	30 Days	21
6	Canada	Ca	visa_0f35cd4379474ec180294082e1f47d22.pdf	1400	t	2026-07-12 11:42:32.912199	North America	Tourist	5-7 Days	30 Days	21
9	Switzerland	CH	visa_e718f7c514304abc8883efe5512ff1fe.pdf	5500	t	2026-07-12 12:13:10.866014	Europe	Tourist	5-7 Days	\N	21
1	Japan	JP	Japan_Visa.pdf	3500	t	2026-06-03 13:36:58.188894	Asia Pacific	Tourist	5-7 Days	30 Days	8
2	South Korea	KR	KOREA_Visa_Requirements.pdf	2400	t	2026-06-03 15:54:48.513913	Asia Pacific	Tourist	5-7 Days	30 Days	21
3	United State	US	visa_56fdaa8e28194c069b32c05b62b81694.pdf	15000	t	2026-06-23 11:37:40.261623	North America	Tourist	5-7 Days	30 Days	12
\.


--
-- Name: agents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.agents_id_seq', 3, true);


--
-- Name: blog_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.blog_posts_id_seq', 4, true);


--
-- Name: contact_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contact_messages_id_seq', 23, true);


--
-- Name: continents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.continents_id_seq', 5, true);


--
-- Name: countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.countries_id_seq', 10, true);


--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_verification_tokens_id_seq', 1, false);


--
-- Name: inquiries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inquiries_id_seq', 179, true);


--
-- Name: inquiry_notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inquiry_notifications_id_seq', 132, true);


--
-- Name: package_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_images_id_seq', 7, true);


--
-- Name: package_reviews_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_reviews_id_seq', 1, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 3, true);


--
-- Name: site_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.site_settings_id_seq', 1, true);


--
-- Name: testimonial_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.testimonial_images_id_seq', 6, true);


--
-- Name: testimonials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.testimonials_id_seq', 11, true);


--
-- Name: tour_packages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tour_packages_id_seq', 21, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 16, true);


--
-- Name: visa_countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.visa_countries_id_seq', 9, true);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: blog_posts blog_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_pkey PRIMARY KEY (id);


--
-- Name: contact_messages contact_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contact_messages
    ADD CONSTRAINT contact_messages_pkey PRIMARY KEY (id);


--
-- Name: continents continents_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.continents
    ADD CONSTRAINT continents_name_key UNIQUE (name);


--
-- Name: continents continents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.continents
    ADD CONSTRAINT continents_pkey PRIMARY KEY (id);


--
-- Name: countries countries_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_name_key UNIQUE (name);


--
-- Name: countries countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_pkey PRIMARY KEY (id);


--
-- Name: email_verification_tokens email_verification_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_pkey PRIMARY KEY (id);


--
-- Name: inquiries inquiries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiries
    ADD CONSTRAINT inquiries_pkey PRIMARY KEY (id);


--
-- Name: inquiry_notifications inquiry_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiry_notifications
    ADD CONSTRAINT inquiry_notifications_pkey PRIMARY KEY (id);


--
-- Name: package_reviews one_review_per_user_per_package; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_reviews
    ADD CONSTRAINT one_review_per_user_per_package UNIQUE (package_id, user_id);


--
-- Name: package_images package_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_images
    ADD CONSTRAINT package_images_pkey PRIMARY KEY (id);


--
-- Name: package_reviews package_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_reviews
    ADD CONSTRAINT package_reviews_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: site_settings site_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site_settings
    ADD CONSTRAINT site_settings_pkey PRIMARY KEY (id);


--
-- Name: testimonial_images testimonial_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonial_images
    ADD CONSTRAINT testimonial_images_pkey PRIMARY KEY (id);


--
-- Name: testimonials testimonials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonials
    ADD CONSTRAINT testimonials_pkey PRIMARY KEY (id);


--
-- Name: tour_packages tour_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_pkey PRIMARY KEY (id);


--
-- Name: users uq_users_oauth_identity; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_oauth_identity UNIQUE (oauth_provider, oauth_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: visa_countries visa_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.visa_countries
    ADD CONSTRAINT visa_countries_pkey PRIMARY KEY (id);


--
-- Name: ix_blog_posts_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_blog_posts_category ON public.blog_posts USING btree (category);


--
-- Name: ix_blog_posts_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_blog_posts_created_at ON public.blog_posts USING btree (created_at);


--
-- Name: ix_blog_posts_is_published; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_blog_posts_is_published ON public.blog_posts USING btree (is_published);


--
-- Name: ix_email_verification_tokens_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_email_verification_tokens_created_at ON public.email_verification_tokens USING btree (created_at);


--
-- Name: ix_email_verification_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_email_verification_tokens_expires_at ON public.email_verification_tokens USING btree (expires_at);


--
-- Name: ix_email_verification_tokens_is_used; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_email_verification_tokens_is_used ON public.email_verification_tokens USING btree (is_used);


--
-- Name: ix_email_verification_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_email_verification_tokens_token ON public.email_verification_tokens USING btree (token);


--
-- Name: ix_email_verification_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_email_verification_tokens_user_id ON public.email_verification_tokens USING btree (user_id);


--
-- Name: ix_inquiries_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiries_created_at ON public.inquiries USING btree (created_at);


--
-- Name: ix_inquiries_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiries_email ON public.inquiries USING btree (email);


--
-- Name: ix_inquiries_last_exported_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiries_last_exported_at ON public.inquiries USING btree (last_exported_at);


--
-- Name: ix_inquiries_reference_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_inquiries_reference_number ON public.inquiries USING btree (reference_number);


--
-- Name: ix_inquiries_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiries_status ON public.inquiries USING btree (status);


--
-- Name: ix_inquiries_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiries_user_id ON public.inquiries USING btree (user_id);


--
-- Name: ix_inquiry_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiry_notifications_created_at ON public.inquiry_notifications USING btree (created_at);


--
-- Name: ix_inquiry_notifications_inquiry_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiry_notifications_inquiry_id ON public.inquiry_notifications USING btree (inquiry_id);


--
-- Name: ix_inquiry_notifications_is_read; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiry_notifications_is_read ON public.inquiry_notifications USING btree (is_read);


--
-- Name: ix_inquiry_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_inquiry_notifications_user_id ON public.inquiry_notifications USING btree (user_id);


--
-- Name: ix_package_images_package_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_package_images_package_id ON public.package_images USING btree (package_id);


--
-- Name: ix_package_reviews_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_package_reviews_created_at ON public.package_reviews USING btree (created_at);


--
-- Name: ix_package_reviews_package_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_package_reviews_package_id ON public.package_reviews USING btree (package_id);


--
-- Name: ix_password_reset_tokens_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_password_reset_tokens_created_at ON public.password_reset_tokens USING btree (created_at);


--
-- Name: ix_password_reset_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_password_reset_tokens_expires_at ON public.password_reset_tokens USING btree (expires_at);


--
-- Name: ix_password_reset_tokens_is_used; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_password_reset_tokens_is_used ON public.password_reset_tokens USING btree (is_used);


--
-- Name: ix_password_reset_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);


--
-- Name: ix_password_reset_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: ix_testimonial_images_testimonial_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_testimonial_images_testimonial_id ON public.testimonial_images USING btree (testimonial_id);


--
-- Name: ix_tour_packages_assigned_agent_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tour_packages_assigned_agent_id ON public.tour_packages USING btree (assigned_agent_id);


--
-- Name: ix_tour_packages_country_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tour_packages_country_id ON public.tour_packages USING btree (country_id);


--
-- Name: ix_tour_packages_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tour_packages_is_active ON public.tour_packages USING btree (is_active);


--
-- Name: ix_tour_packages_is_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tour_packages_is_featured ON public.tour_packages USING btree (is_featured);


--
-- Name: ix_tour_packages_package_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tour_packages_package_type ON public.tour_packages USING btree (package_type);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_email_verified; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_email_verified ON public.users USING btree (email_verified);


--
-- Name: ix_users_is_admin; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_is_admin ON public.users USING btree (is_admin);


--
-- Name: ix_users_oauth_provider; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_oauth_provider ON public.users USING btree (oauth_provider);


--
-- Name: contact_messages contact_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contact_messages
    ADD CONSTRAINT contact_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: countries countries_continent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.countries
    ADD CONSTRAINT countries_continent_id_fkey FOREIGN KEY (continent_id) REFERENCES public.continents(id);


--
-- Name: email_verification_tokens email_verification_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: inquiries inquiries_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiries
    ADD CONSTRAINT inquiries_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.tour_packages(id);


--
-- Name: inquiries inquiries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiries
    ADD CONSTRAINT inquiries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: inquiry_notifications inquiry_notifications_inquiry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiry_notifications
    ADD CONSTRAINT inquiry_notifications_inquiry_id_fkey FOREIGN KEY (inquiry_id) REFERENCES public.inquiries(id);


--
-- Name: inquiry_notifications inquiry_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inquiry_notifications
    ADD CONSTRAINT inquiry_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: package_images package_images_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_images
    ADD CONSTRAINT package_images_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.tour_packages(id);


--
-- Name: package_reviews package_reviews_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_reviews
    ADD CONSTRAINT package_reviews_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.tour_packages(id) ON DELETE CASCADE;


--
-- Name: package_reviews package_reviews_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_reviews
    ADD CONSTRAINT package_reviews_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: testimonial_images testimonial_images_testimonial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonial_images
    ADD CONSTRAINT testimonial_images_testimonial_id_fkey FOREIGN KEY (testimonial_id) REFERENCES public.testimonials(id) ON DELETE CASCADE;


--
-- Name: testimonials testimonials_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.testimonials
    ADD CONSTRAINT testimonials_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tour_packages tour_packages_assigned_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_assigned_agent_id_fkey FOREIGN KEY (assigned_agent_id) REFERENCES public.agents(id);


--
-- Name: tour_packages tour_packages_country_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tour_packages
    ADD CONSTRAINT tour_packages_country_id_fkey FOREIGN KEY (country_id) REFERENCES public.countries(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 0LUeGtFg4IMDlrxYU2IxeZco5KeKoDJ0MbJaq3OTYfCqA4aCr0gbcqdfZTEIIAY

