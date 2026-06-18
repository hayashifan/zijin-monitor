module.exports = {
  apps: [
    {
      name: 'zijin-web',
      cwd: './frontend',
      script: 'npx',
      args: 'serve -s dist -l 5173',
      env: {
        NODE_ENV: 'production',
      },
      max_memory_restart: '200M',
    },
    {
      name: 'zijin-server',
      cwd: './backend',
      script: 'venv/Scripts/python.exe',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 3001',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      max_memory_restart: '500M',
      exp_backoff_restart_delay: 100,
    },
  ],
};
