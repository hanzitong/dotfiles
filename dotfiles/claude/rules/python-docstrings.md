# Python の docstring（すべてのプロジェクトのためのルール）

- すべての関数、メソッド、クラスに、docstring を書く。
- docstring には、まず、その関数やクラスの **目的** を書く。目的を明記することが、最も大事である。
  - 目的とは、「なぜ、この関数やクラスがあるのか」「何のためにあるのか」である。
  - 「何をするか」（処理の手順）だけで終わらせない。手順は、コードを読めば分かる。目的は、コードからは分からない。
- 目的のあとに、必要に応じて、次のことを書く。
  - 引数と戻り値の意味（型ヒントで分かること以上の意味。例: `None` は何を表すか）。
  - 投げる例外。
  - スレッドとの関係（どのスレッドが呼ぶか、共有するデータに触るか）。
- 例（目的が分かる docstring と、分からない docstring）

  ```python
  # 目的が分からない（処理を言い換えているだけ）
  def _update_server_status(...) -> tuple[bool, int]:
      '''Take one health check result and return the new values.'''

  # 目的が分かる
  def _update_server_status(...) -> tuple[bool, int]:
      '''
      Purpose: mark the server as down only after several health checks
      in a row fail, so that one dropped packet does not trigger a failover.
      '''
  ```

- コードのレビューで、docstring のない関数やクラス、目的が書かれていない docstring を見つけたら、ファイル、行、目的の案を添えて指摘する。
