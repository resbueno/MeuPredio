# Imagem de desenvolvimento do frontend MeuPredio (Vite dev server).
# Não otimizada para produção (isso fica para a fase de deploy real na OCI,
# onde o build estático seria servido por um Nginx ou similar).
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
