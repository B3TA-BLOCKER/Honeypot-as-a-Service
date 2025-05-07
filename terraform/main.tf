provider "aws" {
  region = "us-east-1"  # Change this to your preferred AWS region
}

# Dynamically get the latest Ubuntu 20.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security group allowing web and SSH traffic
resource "aws_security_group" "honeypot_sg" {
  name        = "honeypot-sg"
  description = "Allow HTTP, HTTPS, and SSH traffic"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # You should restrict this in production!
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instance to run your honeypot
resource "aws_instance" "honeypot" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"
  key_name               = "HaaS-key"  # Ensure this key exists in AWS
  security_groups        = [aws_security_group.honeypot_sg.name]
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io
              systemctl enable docker
              systemctl start docker
              docker pull your-dockerhub-username/haas-webapp:latest  # Replace with your DockerHub image
              docker run -d -p 80:80 your-dockerhub-username/haas-webapp:latest
              EOF

  tags = {
    Name = "Honeypot-Instance"
  }
}

# Output instance public IP
output "instance_public_ip" {
  value = aws_instance.honeypot.public_ip
}
