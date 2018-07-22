# Copyright © 2018 Necdet Can Ateşman, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

from weakref import WeakKeyDictionary
from elasticsearch import Elasticsearch
from score.init import (
    ConfiguredModule, InitializationError, parse_list, parse_bool,
    extract_conf, parse_time_interval, parse_dotted_path)
from .ctx import CtxProxy
from .dsl import DslExtension


defaults = {
    'keep_source': False,
    'ctx.member': 'es',
    'ctx.extensions': [],
}


def init(confdict, ctx=None):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`args.hosts`
        A list of hosts (as read by :func:`score.init.parse_list`) to pass to
        the :class:`Elasticsearch <elasticsearch.Elasticsearch>` constructor.

    :confkey:`args.*`
        Any other arguments to be passed to the :class:`Elasticsearch
        <elasticsearch.Elasticsearch>` constructor.

    :confkey:`index` :confdefault:`score`
        The index to use in all operations.

    :confkey:`keep_source` :confdefault:`False`
        Whether the `_source` field should be enabled. The default is `False`,
        since the canonical representation of objects should be in a
        database.

    :confkey:`ctx.member` :confdefault:`es`
        The name of the :term:`context member`, that should be registered with
        the configured :mod:`score.ctx` module (if there is one). The default
        value allows one to conveniently query the index:

        >>> for knight in ctx.es.client.search(User, 'name:sir*')
        ...     print(knight.name)

    :confkey:`ctx.extensions`
        Additional extension classes for the context proxy.

    """
    conf = defaults.copy()
    conf.update(confdict)
    connect_kwargs = parse_connect_conf(extract_conf(conf, 'args.'))
    if 'index' not in conf:
        conf['index'] = 'score'
    keep_source = parse_bool(conf['keep_source'])
    ctx_extensions = [DslExtension]
    for path in parse_list(conf['ctx.extensions']):
        class_ = parse_dotted_path(path)
        if not issubclass(class_, CtxProxy):
            raise InitializationError(
                'score.es6',
                'Ctx extensions classes must be sub-classes of CtxProxy')
        ctx_extensions.append(class_)
    es_conf = ConfiguredEs6Module(connect_kwargs, conf['index'], keep_source,
                                  ctx_extensions)
    if ctx and conf['ctx.member'] not in (None, 'None'):
        ctx.register(conf['ctx.member'], es_conf.get_ctx_proxy)
    return es_conf


def parse_connect_conf(conf):
    conf = conf.copy()
    if 'hosts' in conf:
        conf['hosts'] = parse_list(conf['hosts'])
    if 'verify_certs' in conf:
        conf['verify_certs'] = parse_bool(conf['verify_certs'])
    if 'use_ssl' in conf:
        conf['use_ssl'] = parse_bool(conf['use_ssl'])
    if 'timeout' in conf:
        conf['timeout'] = parse_time_interval(conf['timeout'])
    return conf


class ConfiguredEs6Module(ConfiguredModule):
    """
    This module's :class:`configuration class
    <score.init.ConfiguredModule>`.
    """

    def __init__(self, connect_kwargs, index, keep_source, ctx_extensions):
        self.connect_kwargs = connect_kwargs
        self.index = index
        self.keep_source = keep_source
        self._client = None
        self.__ctx_proxies = WeakKeyDictionary()
        self.__ctx_proxy_extensions = list(ctx_extensions)

    def _finalize(self):
        if not self.__ctx_proxy_extensions:
            self.__ctx_proxy = CtxProxy
        else:
            name = 'ConfiguredEs6CtxProxy'
            bases = tuple(self.__ctx_proxy_extensions)
            self.__ctx_proxy = type(name, bases, {})
        self.client

    @property
    def client(self):
        if self._client is None:
            self._client = Elasticsearch(**self.connect_kwargs)
        return self._client

    def destroy(self):
        self.client.indices.delete(index=self.index, ignore=404)

    def create(self, destroy=True):
        if destroy:
            self.destroy()
        self.client.indices.create(index=self.index, ignore=400)

    def register_ctx_proxy_extension(self, extension):
        assert not self._finalized
        if not issubclass(extension, CtxProxy):
            raise ValueError('Extension class must be a sub-class of CtxProxy')
        self.__ctx_proxy_extensions.append(extension)

    def get_ctx_proxy(self, ctx):
        if ctx in self.__ctx_proxies:
            return self.__ctx_proxies[ctx]
        self.__ctx_proxies[ctx] = self.__ctx_proxy(self, ctx)
        return self.__ctx_proxies[ctx]
