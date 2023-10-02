!!! example
    The full source code for this example is available
    [here](https://github.com/lucafaggianelli/plombery/blob/main/examples/src/ssl_certificates.py)

Managing SSL certificate expiration dates manually can be a challenging and error-prone task,
especially in environments with a large number of hostnames to check.

Failing to renew certificates on time can result in unexpected outages and security breaches.
To address this issue, you can use Plombery to automate the monitoring of SSL certificate expiration
dates and receive notifications when a certificate is due to expire.

<figure markdown>
  ![The SSL check pipeline](/plombery/assets/images/recipes/ssl_check.png)
  <figcaption>The SSL check pipeline</figcaption>
</figure>

<figure markdown>
  ![The run page with logs](/plombery/assets/images/recipes/ssl_check_run.png)
  <figcaption>The run page with logs</figcaption>
</figure>

You can also run an SSL check on the fly via the manual trigger:

<figure markdown>
  ![Manual run](/plombery/assets/images/recipes/ssl_check_manual.png)
  <figcaption>Manual run</figcaption>
</figure>

## How to

Define a list of hostnames you want to check and create 1 trigger for each of them so
once a trigger fails you know which hostname is concerned:

```py
--8<-- "examples/src/ssl_certificates.py:14:17"

--8<-- "examples/src/ssl_certificates.py:78:97"
```

The pipeline in this example has only 1 task but you could add additional
checks on the SSL certificate as additional tasks:

```py
--8<-- "examples/src/ssl_certificates.py:57:75"
```

