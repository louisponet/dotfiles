"""
Processors are decorated functions in plugins that inject filters, adorners
or keybindings in the main application
"""

import logging


logger = logging.getLogger(__name__)


class _Processor:
    def __init__(self, fn=None, active=True, order=0, instance=None, **kwargs):
        self.__doc__ = fn.__doc__
        self.fn = fn
        self.active = active
        self.order = order
        self.kwargs = kwargs
        self.self = instance

    def __call__(self):
        return self.fn(self.self, **self.kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.__class__(fn=self.fn, active=self.active,
                              order=self.order, instance=instance, **self.kwargs)


class _NodeProcessor(_Processor):
    def __call__(self, node):
        return self.fn(self.self, node)


class _processor:
    order = 0
    processor_classes = []

    def __init_subclass__(cls, processor_class, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.processor_class = processor_class
        _processor.processor_classes.append(processor_class)

    def __init__(self, active=True, **kwargs):
        self.active = active
        self.kwargs = kwargs

    def __call__(self, fn):
        # if 'bindings' in self.kwargs:
        #     raise Exception((self.active, self.kwargs))
            # raise Exception(self.__class__.processor_class)
        logger.debug("*************************")
        logger.debug(self.kwargs)
        f = self.__class__.processor_class(fn=fn, active=self.active,
                                           order=self.__class__.order,
                                           **self.kwargs)
        self.__class__.order += 1
        return f


class Binding(_Processor):
    reg_name = "_key_bindings"

    def __init__(self, bindings=None, mode=None, **kwargs):
        logger.debug("init %s", bindings)
        self.bindings = bindings
        self.mode = mode
        super().__init__(**kwargs)


class key_binding(_processor, processor_class=Binding):
    def __init__(self, mode, *bindings, **kwargs):
        kwargs["bindings"] = bindings
        kwargs["mode"] = mode
        logger.debug(kwargs)
        super().__init__(False, **kwargs)


class Filter(_NodeProcessor):
    reg_name = "_filters"
    pass


class filter(_processor, processor_class=Filter):
    pass


class Adorner(_NodeProcessor):
    reg_name = "_adorners"
    pass


class adorner(_processor, processor_class=Adorner):
    pass


class Refresher(_Processor):
    reg_name = "_refreshers"
    pass


class refresher(_processor, processor_class=Refresher):
    pass


class ProcessorProviderMeta(type):
    def __new__(metacls, name, bases, attrs):
        # import ipdb; ipdb.set_trace()
        for proc_class in _processor.processor_classes:
            attrs[proc_class.reg_name] = procs = {}
            for b in bases:
                if hasattr(b, proc_class.reg_name):
                    procs.update(getattr(b, proc_class.reg_name))
            for k, attr in attrs.items():
                if isinstance(attr, proc_class):
                    procs[k] = attr

        new = super().__new__(metacls, name, bases, attrs)
        old_init = new.__init__
        if old_init is object.__init__:
            old_init = lambda x: None

        def new_init(self, *args, **kwargs):
            for proc_class in _processor.processor_classes:
                instance_reg = getattr(self, proc_class.reg_name, {})
                setattr(self, proc_class.reg_name, instance_reg)
                instance_reg.update({
                    k: getattr(self, k) for k in
                    getattr(self.__class__, proc_class.reg_name)
                })
                setattr(self, proc_class.reg_name, instance_reg)
            old_init(self, *args, **kwargs)

        new.__init__ = new_init
        return new


class ProcessorProvider(metaclass=ProcessorProviderMeta):
    def __init__(self):
        super().__init__()

    def add_bindings_for_mode(self, mode, kb):
        for k, b in self._key_bindings.items():
            logger.debug((k, b))
            # logger.debug(b.mode)
            logger.debug(mode)
            if b.mode is mode:
                for bi in b.bindings:
                    kb.add(*bi)(getattr(self, k))
