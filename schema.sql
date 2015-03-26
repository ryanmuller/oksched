drop table if exists teachers;
create table teachers (
  id integer primary key autoincrement,
  name text not null
);

drop table if exists students;
create table students (
  id integer primary key autoincrement,
  name text not null
);

drop table if exists availabilities;
create table availabilities (
  teacher_id integer not null,
  start_time text not null,
  unique (teacher_id, start_time) on conflict replace
);


drop table if exists appointments;
create table appointments (
  student_id integer not null,
  teacher_id integer not null,
  start_time text not null,
  unique (student_id, start_time) on conflict replace
);
-- store availability id so that we can warn if that availability is modified
-- if availability is deleted, start time is also stored so that another match can be made

insert into teachers (name) values ('curly'), ('larry'), ('moe');
insert into students (name) values ('leo');
insert into availabilities (teacher_id, start_time) values (1, '2015-03-26 12:00'),
                                                           (2, '2015-03-26 02:00'),
                                                           (3, '2015-03-27 15:30');
