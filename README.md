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
select left(cf.title, 64), cf.url, cf.latest_mail
from commitfest as cf
left join cputube as ct on ct.url = cf.url
where status = 'Ready for Committer' and ct.apply_passing and ct.build_passing
order by latest_mail desc;
```

References:
* https://commitfest.postgresql.org/
* http://commitfest.cputube.org/
* https://postgr.es/m/CAB7nPqSrHF%2BkNQ6Eq2uy91RcysoCzQr1AjOjkuCn9jvMdJZ6Fw%40mail.gmail.com
* https://postgr.es/m/20180302090315.GA29307%40e733.localdomain
