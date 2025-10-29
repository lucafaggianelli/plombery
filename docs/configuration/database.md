Plombery is database-agnostic and relies on the SQLAlchemy ORM to connect to a DB,
it means that it can work with any DB suuported by SQLAlchemy.

## Libsql / Turso (SQLite)

Libsql hosted on Turso cloud is a great option for Plombery as it's a lightweight DB
based on SQLite that has the advantage of being hosted on the cloud by Turso (the maker of Libsql),
which offer 100 DBs for free!

To use a Libsql DB with Plombery you need to need to install the package `sqlalchemy-libsql`
which provide the right dialect for SQLAlchemy, for more info see [sqlalchemy-libsql on pypi](https://pypi.org/project/sqlalchemy-libsql/):

```sh
uv add sqlalchemy-libsql
```

Then the `database_url` configuration must start with `sqlite+libsql://` and not with `libsql://`.

You can use local libsql instances (which are just files like SQLite) or instances hosted on Turso.
If you create an instance on Turso, be sure to also add the config `database_auth_token`.
