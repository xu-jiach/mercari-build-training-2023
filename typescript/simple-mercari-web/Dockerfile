# Use the official Node.js 18 image from Docker Hub
FROM node:18-alpine

# Add a new group and user
RUN addgroup -S mercari && adduser -S trainee -G mercari

# Set the working directory to /app
WORKDIR /app

COPY . /app

WORKDIR /app/typescript/simple-mercari-web

# Install project dependencies
RUN npm ci

# Change ownership of the /home directory to trainee
RUN chown -R trainee:mercari /app/typescript/simple-mercari-web

# Switch to the new user
USER trainee

# Run your app
CMD [ "npm", "start" ]
