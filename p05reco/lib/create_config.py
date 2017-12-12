import configobj

def createConfig(path, identifier=None, name=None)
    config = configobj(path)
    config['config']['allow_config_alteration'] = True
    config['config']['allow_copying'] = True
    config['output']['path'] = ''
    config['preprocessing']['bin'] = 2
    config['preprocessing']['horizontal_roi'] = []
    config['preprocessing']['vertical_roi'] = []


