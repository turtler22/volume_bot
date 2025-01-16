# Install Docker TBD
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Build and run
docker build -t telegram-bot .
docker run -d \
  --name telegram-bot \
  --restart unless-stopped \
  --env-file .env \
  telegram-bot