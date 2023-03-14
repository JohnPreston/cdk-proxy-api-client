#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>


def get_module(module_name) -> tuple:
    from importlib import import_module

    try:
        res_module = import_module(module_name)
        try:
            module = getattr(res_module, "COMPOSE_X_MODULES")
            return res_module, module
        except AttributeError:
            print(f"No {module_name}.COMPOSE_X_MODULES found")
    except AttributeError as error:
        print(error)
        return None, None
    except ImportError as error:
        print(error)
        return None, None
