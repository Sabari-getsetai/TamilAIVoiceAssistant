FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

EXPOSE 3000

# Run in development mode with hot-reload
CMD ["npm", "run", "dev"]
