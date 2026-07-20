--
-- PostgreSQL database dump
--

\restrict Rb2vhCLYOMHSKijzywawBAWCf6g1hv54h2Zku664Aoq1hdGmtFuvR6kOLZpvoZN

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

--
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agents (id, name, email, notes, is_active, created_at, is_visa_agent) FROM stdin;
1	Boji	claude6.afk@gmail.com	Newcoast Boracay	t	2026-06-28 14:27:38.475625	f
3	bojis	10claudeuser@gmail.com	\N	t	2026-06-28 15:19:49.931813	t
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
-- Name: continents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.continents_id_seq', 5, true);


--
-- Name: countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.countries_id_seq', 10, true);


--
-- Name: package_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.package_images_id_seq', 7, true);


--
-- Name: tour_packages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tour_packages_id_seq', 21, true);


--
-- Name: visa_countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.visa_countries_id_seq', 9, true);


--
-- PostgreSQL database dump complete
--

\unrestrict Rb2vhCLYOMHSKijzywawBAWCf6g1hv54h2Zku664Aoq1hdGmtFuvR6kOLZpvoZN

