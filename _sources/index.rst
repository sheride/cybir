cybir: Birational geometry of Calabi-Yau threefolds
====================================================

**cybir** is a Python package for studying the birational geometry of
Calabi-Yau threefold hypersurfaces in toric varieties, following the
methods of `arXiv:2212.10573 <https://arxiv.org/abs/2212.10573>`_ and
`arXiv:2303.00757 <https://arxiv.org/abs/2303.00757>`_.

The package reconstructs the extended Kahler cone (EKC) from
genus-zero Gopakumar-Vafa invariants and integrates cleanly with
`CYTools <https://cytools.liagre.fr/>`_.

Features:

- BFS-based EKC construction with adaptive GV degree
- Classification of extremal contractions (asymptotic, CFT, su(2),
  symmetric flop, generic flop)
- Coxeter group construction and orbit expansion for the full
  birational geometry
- CYTools monkey-patching for seamless integration
- On-demand GV reconstruction for any phase


Table of contents
-----------------

.. toctree::
   :maxdepth: 1
   :caption: API Documentation

   cybir
   cybir.core

.. toctree::
   :maxdepth: 1
   :caption: Examples

   notebooks/h11_2_survey
   notebooks/h11_2_walkthrough
   notebooks/h11_3_walkthrough


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
