CREATE TABLE public.api_emailverificationcode (
    id bigint NOT NULL,
    email character varying(254) NOT NULL,
    code character varying(6) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    is_used boolean NOT NULL
);

CREATE TABLE public.custom_user (
    id bigint NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    email character varying(254) NOT NULL,
    phone character varying(15),
    avatar character varying(200),
    role character varying(10) NOT NULL,
    department character varying(100),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    bio text NOT NULL,
    birthday date,
    gender character varying(10),
    nickname character varying(50),
    nickname_approved character varying(20),
    nickname_candidate character varying(20),
    nickname_reject_reason character varying(255) NOT NULL,
    nickname_reviewed_at timestamp with time zone,
    nickname_reviewed_by_id bigint,
    nickname_status character varying(10) NOT NULL
);

CREATE TABLE public.leetcode_problem (
    id bigint NOT NULL,
    problem_id integer NOT NULL,
    title character varying(200) NOT NULL,
    title_slug character varying(200) NOT NULL,
    difficulty character varying(10) NOT NULL,
    is_premium boolean NOT NULL,
    content text NOT NULL,
    acceptance_rate double precision NOT NULL,
    submission_count integer NOT NULL,
    accepted_count integer NOT NULL,
    tags jsonb NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

CREATE TABLE public.nickname_review_log (
    id bigint NOT NULL,
    action character varying(20) NOT NULL,
    nickname_value character varying(20) NOT NULL,
    hit_rule character varying(64) NOT NULL,
    message character varying(255) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    operator_id bigint,
    user_id bigint NOT NULL
);

CREATE TABLE public.problem_completion (
    id bigint NOT NULL,
    status character varying(15) NOT NULL,
    attempts integer NOT NULL,
    last_attempted timestamp with time zone,
    completed_at timestamp with time zone,
    solution_code text NOT NULL,
    notes text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    problem_id bigint NOT NULL,
    user_id bigint NOT NULL
);

CREATE TABLE public.problem_tag (
    id bigint NOT NULL,
    name character varying(50) NOT NULL,
    slug character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL
);

CREATE TABLE public.user_activity (
    id bigint NOT NULL,
    activity_type character varying(20) NOT NULL,
    ip_address inet,
    user_agent text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    problem_id bigint,
    user_id bigint NOT NULL
);

