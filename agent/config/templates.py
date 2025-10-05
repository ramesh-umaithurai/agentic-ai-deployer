"""Configuration templates for different deployment scenarios"""

CLOUDRUN_DEFAULT_CONFIG = {
    'cpu': '1',
    'memory': '2Gi',
    'max_instances': 10,
    'concurrency': 80,
    'timeout_seconds': 300
}

DATABASE_TIERS = {
    'development': 'db-f1-micro',
    'staging': 'db-g1-small',
    'production': 'db-n1-standard-1'
}

REGIONS = {
    'us-central1': 'Iowa, USA',
    'us-east1': 'South Carolina, USA',
    'us-west1': 'Oregon, USA',
    'europe-west1': 'Belgium, EU',
    'asia-east1': 'Taiwan, Asia'
}

DOTNET_VERSIONS = {
    '6.0': 'mcr.microsoft.com/dotnet/aspnet:6.0',
    '7.0': 'mcr.microsoft.com/dotnet/aspnet:7.0',
    '8.0': 'mcr.microsoft.com/dotnet/aspnet:8.0'
}