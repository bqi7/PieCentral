Generating Documentation Using Sphinx
=====================================

API documentation for Runtime and Hibike is automatically generated from docstrings using
[Sphinx](http://www.sphinx-doc.org/en/stable/).

Prerequisites
-------------

You need to have installed Sphinx. This can be done through PyPI.

```bash
pip install sphinx
```

In addition, you will need Make if you want to use the Makefiles.

Building Existing Docs
----------------------

Hibike and Runtime's documentation are located within their respective folders in `docs`. Sphinx uses a format
called [ReStructuredText](http://www.sphinx-doc.org/en/stable/rest.html) (RST).
Although we can 

At the root of each of these directories is an `index.rst` file. This file contains a table of contents,
which should look something like

```
.. toctree::
    :maxdepth 4:
    :caption: Contents

    module1
    module2
```

These entries (`module1` and so forth) reference other `.rst` files.