FROM node:20-alpine

WORKDIR /app

# Copiamos solo package.json para instalar dependencias
COPY package.json ./

RUN npm install

# Ahora copiamos el resto del código
COPY . .

EXPOSE 3000

# Arrancar Next.js en modo dev
CMD ["npm", "run", "dev"]
