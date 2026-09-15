# --- Stage 1: builder ---
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgdk-pixbuf-2.0-0 \
    libldap2-dev \
    libpq-dev \
    libsasl2-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff-dev \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

# wkhtmltopdf
RUN curl -sL -o /tmp/wkhtmltox.deb \
    https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && dpkg -x /tmp/wkhtmltox.deb /tmp/wkhtmltox

# --- Stage 2: runtime ---
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    ODOO_RC=/etc/odoo/odoo.conf

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    fonts-noto-cjk \
    git \
    libgdk-pixbuf-2.0-0 \
    libldap-2.5-0 \
    libpq5 \
    libsasl2-2 \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libfreetype6 \
    liblcms2-2 \
    libwebp7 \
    libtiff6 \
    libssl3 \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy pip-installed packages from builder
COPY --from=builder /install /usr/local

# Copy wkhtmltopdf from builder
COPY --from=builder /tmp/wkhtmltox/usr/local/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
COPY --from=builder /tmp/wkhtmltox/usr/local/lib/ /usr/local/lib/
RUN ldconfig

# Odoo system user
RUN groupadd -r odoo && useradd -r -g odoo -d /var/lib/odoo -s /bin/false odoo

RUN mkdir -p /var/lib/odoo /etc/odoo /opt/odoo \
    && chown -R odoo:odoo /var/lib/odoo /etc/odoo /opt/odoo

# Minimal config — admin_passwd is NOT set here; it must come from ODOO_ADMIN_PASSWD env var
RUN printf '[options]\naddons_path = /opt/odoo/addons\n' > /etc/odoo/odoo.conf \
    && chown odoo:odoo /etc/odoo/odoo.conf

WORKDIR /opt/odoo

EXPOSE 8069

USER odoo

CMD ["odoo-bin", "--config=/etc/odoo/odoo.conf"]
