# py-autoreviewer

Scripts for building some analytics on current PostgreSQL commitfest.

Usage:

```bash
./commitfest-export.py https://commitfest.postgresql.org/17/ > commitfest.sql
./cputube-export.py | tee cputube.sql

psql < commitfest.sql
psql < cputube.sql
```

Now for instant you want to find all patches that have "Ready for Commiter"
status, apply and pass all tests:

```sql
select left(cf.title, 64) as title, cf.url, cf.latest_mail
from commitfest as cf
left join cputube as ct on ct.url = cf.url
where status = 'Ready for Committer' and ct.apply_passing and ct.build_passing
order by latest_mail desc;
```

Or, if you want to notify authors whose patches have "Ready for Committer"
status, but don't apply or don't pass tests:

```sql
select left(cf.title, 64) as title, cf.url, cf.latest_mail, ct.apply_passing, ct.build_passing
from commitfest as cf
left join cputube as ct on ct.url = cf.url
where status = 'Ready for Committer' and (not ct.apply_passing or not ct.build_passing)
order by latest_mail desc;
```

Stats on number of patches submitted and reviewed per person:

```sql
create materialized view reviewers_stat
  as select unnest(string_to_array(reviewers, ', ')) as reviewer,
            count(*) as cnt
     from commitfest
     group by reviewer
     order by cnt desc;

create materialized view authors_stat
  as select unnest(string_to_array(authors, ', ')) as author,
            count(*) as cnt
     from commitfest
     group by author
     order by cnt desc;

select coalesce(r.reviewer, a.author) as person,
       coalesce(r.cnt, 0) as rcnt,
       coalesce(a.cnt, 0) as acnt,
       (coalesce(r.cnt, 0) - coalesce(a.cnt, 0)) as delta
from reviewers_stat as r
full join authors_stat as a on r.reviewer = a.author
order by delta desc;
```

References:
* https://commitfest.postgresql.org/
* http://commitfest.cputube.org/
* https://postgr.es/m/CAB7nPqSrHF%2BkNQ6Eq2uy91RcysoCzQr1AjOjkuCn9jvMdJZ6Fw%40mail.gmail.com
* https://postgr.es/m/20180302090315.GA29307%40e733.localdomain
