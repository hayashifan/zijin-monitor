module.exports = {
  apps: [
    {
      name: 'zijin-web',
      cwd: './frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 5174 --host',
      interpreter: 'node',
      env: {
        NODE_ENV: 'development',
      },
      max_memory_restart: '300M',
    },
    {
      name: 'zijin-server',
      cwd: './backend',
      script: 'venv/Scripts/python.exe',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 3002',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      max_memory_restart: '500M',
      exp_backoff_restart_delay: 100,
    },
  ],
};
