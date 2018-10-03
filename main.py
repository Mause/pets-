import os
import pickle
from itertools import chain
from concurrent.futures import ThreadPoolExecutor as PoolExectutor

from tqdm import tqdm
from redis import StrictRedis
from flask import Flask, render_template, jsonify

from sources import sources, default

redis = StrictRedis.from_url(os.environ.get("REDIS_URL"))

EXECUTOR = PoolExectutor()
app = Flask(__name__)
app.json_encoder.default = lambda self, obj: default(obj)


def get_data():
    data = chain.from_iterable(
        EXECUTOR.map(
            lambda func: list(func()),
            sources,
        )
    )
    return sorted(
        tqdm(data),
        key=lambda item: item.found_on,
        reverse=True
    )


def get_cached_data():
    return pickle.loads(redis.get('data'))


@app.route('/index.json')
def index_json():
    return jsonify(
        data=get_cached_data(),
        last_updated=redis.get('last_updated')
    )


@app.route('/')
def index():
    return render_template(
        'index.html',
        data=get_cached_data(),
        last_updated=redis.get('last_updated')
    )


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )
