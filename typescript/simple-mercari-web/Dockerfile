# Use the official Node.js 16 image from Docker Hub
FROM node:18-alpine

# Add a new group and user
RUN addgroup -S mercari && adduser -S trainee -G mercari

# Set the working directory to /app
WORKDIR /home

COPY typescript typescript

# Copy the package.json and package-lock.json


WORKDIR /home/typescript/simple-mercari-web

# Install project dependencies
RUN npm install

# Change ownership of the /app directory to trainee
RUN chown -R trainee:mercari /home/typescript/simple-mercari-web

# Switch to the new user
USER trainee

# Run your app
CMD [ "npm", "start" ]
