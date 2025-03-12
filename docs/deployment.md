# Deployment

## Checklist

Be sure to have configured your app for production, by checking the values of the following configuration parameters:
- `database_url`
- `allowed_origins`
- `frontend_url`

## Run the app

Here is how to run the app with uvicorn, allowing external connection:
```sh
uvicorn app:app --host 0.0.0.0
```
