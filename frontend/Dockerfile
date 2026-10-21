# Stage 1: Build the React application
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY . .

# Build the production application
RUN npm run build


# Stage 2: Serve the production build
FROM nginx:alpine

# Copy built files to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose web server port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]