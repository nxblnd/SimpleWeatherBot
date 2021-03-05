create table cities
(
    id   integer primary key,
    name text,
    lat  real,
    lon  real,
    unique (name, lat, lon)
);
create table users
(
    id              integer primary key,
    user_id         integer unique,
    default_city_id integer,
    foreign key (default_city_id) references cities (id)
);