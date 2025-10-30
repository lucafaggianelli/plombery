Plombery is database-agnostic and relies on the SQLAlchemy ORM to connect to a DB,
it means that it can work with any DB suuported by SQLAlchemy.

## Libsql (SQLite)

Libsql hosted on Turso cloud is a great option for Plombery as it's a lightweight DB
based on SQLite that has the advantage of being hosted on the cloud by Turso (the maker of Libsql),
which offer 100 DBs for free!

To use a Libsql DB with Plombery you need to need to install the package `sqlalchemy-libsql`
which provide the right dialect for SQLAlchemy, for more info see
[sqlalchemy-libsql on pypi](https://pypi.org/project/sqlalchemy-libsql/):

```sh
uv add sqlalchemy-libsql
```

Then the `database_url` configuration must start with `sqlite+libsql://` and not with `libsql://`.

You can use local libsql instances (which are just files like SQLite) or instances hosted on Turso.

### Turso cloud

If you are using an instance hosted on Turso, be sure to add the config
`database_auth_token` with the token generated on the Turso platform.

Finally, the `database_url` should include the query param `?secure=true`, for example:

```
sqlite+libsql://plombery-myuser.aws-eu-west-1.turso.io?secure=true
```
