"""Desktop demo: same as ``greensim view``. Accepts the same options (see ``greensim view -h``).

For screenshots or LIDAR files use ``greensim render`` / ``greensim scan``.
"""

import sys

from greensim.cli import main

if __name__ == "__main__":
    main(["view", *sys.argv[1:]])
