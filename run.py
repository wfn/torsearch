from torsearch import app
import config

app.run(debug = config.DEBUG, host=config.BIND_HOST, port=config.BIND_PORT, threaded=True)
