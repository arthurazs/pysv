from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            name="pysv.c_package.publisher",
            sources=[
                "src/pysv/c_package/new_publisher.c",
            ],
            optional=False,
        ),
    ],
)
