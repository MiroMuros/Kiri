# Installation and Deployment Guide - Clothing Pattern Generator

This guide provides detailed instructions for installing and deploying the Clothing Pattern Generator application in various environments.

## Prerequisites

Before installing the application, ensure your system meets the following requirements:

- **Operating System**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+
- **Python**: Version 3.8 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 2GB minimum
- **Additional Software**: Git (for cloning the repository)

## Development Installation

Follow these steps to set up the application for development:

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/clothing-pattern-generator.git
cd clothing-pattern-generator
```

### 2. Create a Virtual Environment (Recommended)

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Required Directories

```bash
mkdir -p /tmp/clothing_pattern_app/uploads
mkdir -p /tmp/clothing_pattern_app/output
```

### 5. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:5000`.

## Production Deployment

For production environments, we recommend the following setup:

### Option 1: Standalone Server Deployment

#### 1. Install Required Packages

```bash
# Install Python and required system packages
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx

# Clone the repository
git clone https://github.com/your-organization/clothing-pattern-generator.git
cd clothing-pattern-generator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 2. Configure Gunicorn

Create a systemd service file for the application:

```bash
sudo nano /etc/systemd/system/clothing-pattern-generator.service
```

Add the following content:

```
[Unit]
Description=Clothing Pattern Generator
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/clothing-pattern-generator
Environment="PATH=/path/to/clothing-pattern-generator/venv/bin"
ExecStart=/path/to/clothing-pattern-generator/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 "main:flask_app"
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable clothing-pattern-generator
sudo systemctl start clothing-pattern-generator
```

#### 3. Configure Nginx

Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/clothing-pattern-generator
```

Add the following content:

```
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/clothing-pattern-generator/src/ui/static;
    }

    client_max_body_size 16M;
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/clothing-pattern-generator /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Option 2: Docker Deployment

#### 1. Create a Dockerfile

Create a file named `Dockerfile` in the project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

RUN mkdir -p /tmp/clothing_pattern_app/uploads
RUN mkdir -p /tmp/clothing_pattern_app/output

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:flask_app"]
```

#### 2. Create a Docker Compose File

Create a file named `docker-compose.yml`:

```yaml
version: '3'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - uploads:/tmp/clothing_pattern_app/uploads
      - output:/tmp/clothing_pattern_app/output
    restart: always

volumes:
  uploads:
  output:
```

#### 3. Build and Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at `http://localhost:5000`.

## Cloud Deployment

### AWS Elastic Beanstalk Deployment

#### 1. Prepare the Application

Create a file named `.ebextensions/01_flask.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: main:flask_app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current"
```

#### 2. Install the EB CLI

```bash
pip install awsebcli
```

#### 3. Initialize and Deploy

```bash
eb init -p python-3.8 clothing-pattern-generator
eb create clothing-pattern-env
```

### Google Cloud Run Deployment

#### 1. Build the Docker Image

```bash
gcloud builds submit --tag gcr.io/your-project-id/clothing-pattern-generator
```

#### 2. Deploy to Cloud Run

```bash
gcloud run deploy clothing-pattern-generator \
  --image gcr.io/your-project-id/clothing-pattern-generator \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi
```

## Environment Variables

The application supports the following environment variables for configuration:

- `UPLOAD_FOLDER`: Directory for storing uploaded images (default: `/tmp/clothing_pattern_app/uploads`)
- `OUTPUT_FOLDER`: Directory for storing generated patterns (default: `/tmp/clothing_pattern_app/output`)
- `MAX_CONTENT_LENGTH`: Maximum upload size in bytes (default: 16MB)
- `DEBUG`: Enable debug mode (default: `False` in production)
- `PORT`: Port to run the application on (default: `5000`)

## Troubleshooting

### Common Issues

1. **Application fails to start**
   - Check if the required directories exist and have proper permissions
   - Verify that all dependencies are installed correctly
   - Check if the port is already in use by another application

2. **File upload issues**
   - Ensure the upload directory has write permissions
   - Check if the maximum file size is configured correctly
   - Verify that the web server is configured to allow large file uploads

3. **Pattern generation fails**
   - Check the application logs for specific error messages
   - Verify that the output directory has write permissions
   - Ensure there is sufficient memory available for processing

### Checking Logs

#### Standalone Server
```bash
sudo journalctl -u clothing-pattern-generator
```

#### Docker
```bash
docker-compose logs app
```

#### Elastic Beanstalk
```bash
eb logs
```

## Maintenance

### Backup and Restore

It's recommended to regularly backup the following:

1. Application code
2. User-uploaded images (from the `UPLOAD_FOLDER`)
3. Generated patterns (from the `OUTPUT_FOLDER`)

### Updates

To update the application:

1. Pull the latest code from the repository
2. Install any new dependencies
3. Restart the application

## Security Considerations

1. **File Uploads**: The application validates file types and sizes, but additional security measures may be needed in high-security environments
2. **API Endpoints**: Consider adding authentication for API endpoints in production
3. **HTTPS**: Always use HTTPS in production environments
4. **Regular Updates**: Keep all dependencies updated to patch security vulnerabilities

## Performance Optimization

For high-traffic deployments, consider:

1. **Caching**: Implement Redis or Memcached for caching
2. **Load Balancing**: Set up multiple application instances behind a load balancer
3. **CDN**: Use a Content Delivery Network for static assets
4. **Database**: Add a database for storing user data and patterns instead of the filesystem

## Support

For additional support:
- Check the technical documentation
- Visit our community forum
- Contact support at support@clothingpatterngenerator.com
