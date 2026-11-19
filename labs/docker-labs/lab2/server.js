const app = require('express')();
app.get('/', (_, res) => res.send('v1\n'));
const srv = app.listen(3000, () => console.log('listening'));
process.on('SIGTERM', () => { console.log('SIGTERM, closing'); srv.close(() => process.exit(0)); });
