module.exports = {
  apps: [
    {
      name: "fundos-backend",
      script: "./.venv/bin/uvicorn",
      args: "src.main:app --host 0.0.0.0 --port 8000",
      interpreter: "./.venv/bin/python3",
      watch: false,
      autorestart: true,
      max_restarts: 5,
      env: {
        ENVIRONMENT: "production"
      }
    }
  ]
};