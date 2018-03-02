# py-autoreviewer

Scripts for building some analytics on current PostgreSQL commitfest.

Usage:

```
./commitfest-export.py https://commitfest.postgresql.org/17/ > commitfest.sql
./cputube-export.py | tee cputube.sql

psql < commitfest.sql
psql < cputube.sql
```

References:
* https://commitfest.postgresql.org/
* http://commitfest.cputube.org/
* https://postgr.es/m/CAB7nPqSrHF%2BkNQ6Eq2uy91RcysoCzQr1AjOjkuCn9jvMdJZ6Fw%40mail.gmail.com
* https://postgr.es/m/20180302090315.GA29307%40e733.localdomain
