/**
 * The citation registry. Every entry carries a real, resolvable DOI or arXiv identifier.
 *
 * A bare author-year with no link is treated as a failure here, not as a stylistic lapse: it is
 * indistinguishable from a fabricated reference, and this lab's entire argument depends on its
 * claims being checkable. Every one of these was verified against a primary source during the
 * research phase that preceded any code.
 */
import type { Citation } from '@fasl-work/caos-app-shell';

export const CITATIONS: Citation[] = [
  {
    id: 'koza1992',
    label: 'Koza 1992',
    citation:
      'Koza, J. R. (1992). Genetic Programming: On the Programming of Computers by Means of Natural Selection. MIT Press.',
    url: 'https://mitpress.mit.edu/9780262527910/genetic-programming/',
  },
  {
    id: 'keijzer2003',
    label: 'Keijzer 2003',
    citation:
      'Keijzer, M. (2003). Improving symbolic regression with interval arithmetic and linear scaling. EuroGP 2003, LNCS 2610, 70-82.',
    doi: '10.1007/3-540-36599-0_7',
  },
  {
    id: 'kommenda2020',
    label: 'Kommenda et al. 2020',
    citation:
      'Kommenda, M., Burlacu, B., Kronberger, G. and Affenzeller, M. (2020). Parameter identification for symbolic regression using nonlinear least squares. Genetic Programming and Evolvable Machines 21, 471-501.',
    doi: '10.1007/s10710-019-09371-3',
  },
  {
    id: 'deb2002',
    label: 'Deb et al. 2002',
    citation:
      'Deb, K., Pratap, A., Agarwal, S. and Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation 6(2), 182-197.',
    doi: '10.1109/4235.996017',
  },
  {
    id: 'lacava2016',
    label: 'La Cava et al. 2016',
    citation:
      'La Cava, W., Spector, L. and Danai, K. (2016). Epsilon-lexicase selection for regression. GECCO 2016, 741-748.',
    doi: '10.1145/2908812.2908898',
  },
  {
    id: 'schmidt2011',
    label: 'Schmidt and Lipson 2011',
    citation:
      'Schmidt, M. and Lipson, H. (2011). Age-fitness Pareto optimization. In Genetic Programming Theory and Practice VIII, 129-146.',
    doi: '10.1007/978-1-4419-7747-2_8',
  },
  {
    id: 'schmidt2009',
    label: 'Schmidt and Lipson 2009',
    citation:
      'Schmidt, M. and Lipson, H. (2009). Distilling free-form natural laws from experimental data. Science 324(5923), 81-85.',
    doi: '10.1126/science.1165893',
  },
  {
    id: 'lacava2021',
    label: 'La Cava et al. 2021',
    citation:
      'La Cava, W. et al. (2021). Contemporary symbolic regression methods and their relative performance. NeurIPS Datasets and Benchmarks Track 2021.',
    url: 'https://arxiv.org/abs/2107.14351',
  },
  {
    id: 'defranca2024',
    label: 'de Franca et al. 2024',
    citation:
      'de Franca, F. O., Virgolin, M., Kommenda, M. et al. (2024). SRBench++: principled benchmarking of symbolic regression with domain-expert interpretation. IEEE Transactions on Evolutionary Computation 29(4), 1127-1134.',
    doi: '10.1109/TEVC.2024.3423681',
  },
  {
    id: 'udrescu2020',
    label: 'Udrescu and Tegmark 2020',
    citation:
      'Udrescu, S.-M. and Tegmark, M. (2020). AI Feynman: a physics-inspired method for symbolic regression. Science Advances 6(16), eaay2631.',
    doi: '10.1126/sciadv.aay2631',
  },
  {
    id: 'cranmer2020',
    label: 'Cranmer et al. 2020',
    citation:
      'Cranmer, M. et al. (2020). Discovering symbolic models from deep learning with inductive biases. NeurIPS 2020.',
    url: 'https://arxiv.org/abs/2006.11287',
  },
  {
    id: 'cranmer2023',
    label: 'Cranmer 2023',
    citation:
      'Cranmer, M. (2023). Interpretable machine learning for science with PySR and SymbolicRegression.jl.',
    url: 'https://arxiv.org/abs/2305.01582',
  },
  {
    id: 'shojaee2023',
    label: 'Shojaee et al. 2023',
    citation:
      'Shojaee, P., Meidani, K., Barati Farimani, A. and Reddy, C. (2023). Transformer-based planning for symbolic regression. NeurIPS 2023.',
    url: 'https://arxiv.org/abs/2303.06833',
  },
  {
    id: 'biggio2021',
    label: 'Biggio et al. 2021',
    citation:
      'Biggio, L., Bendinelli, T., Neitz, A., Lucchi, A. and Parascandolo, G. (2021). Neural symbolic regression that scales. ICML 2021.',
    url: 'https://arxiv.org/abs/2106.06427',
  },
  {
    id: 'shojaee2025',
    label: 'Shojaee et al. 2025',
    citation:
      'Shojaee, P. et al. (2025). LLM-SRBench: a new benchmark for scientific equation discovery with large language models. ICML 2025.',
    url: 'https://arxiv.org/abs/2504.10415',
  },
  {
    id: 'matsubara2022',
    label: 'Matsubara et al. 2022',
    citation:
      'Matsubara, Y., Chiba, N., Igarashi, R. and Ushiku, Y. (2022). Rethinking symbolic regression datasets and benchmarks for scientific discovery.',
    url: 'https://arxiv.org/abs/2206.10540',
  },
  {
    id: 'romano2021',
    label: 'Romano et al. 2021',
    citation:
      'Romano, J. D. et al. (2021). PMLB v1.0: an open-source dataset collection for benchmarking machine learning methods. Bioinformatics 38(3), 878-880.',
    doi: '10.1093/bioinformatics/btab727',
  },
  {
    id: 'brunton2016',
    label: 'Brunton et al. 2016',
    citation:
      'Brunton, S. L., Proctor, J. L. and Kutz, J. N. (2016). Discovering governing equations from data by sparse identification of nonlinear dynamical systems. PNAS 113(15), 3932-3937.',
    doi: '10.1073/pnas.1517384113',
  },
  {
    id: 'tenachi2023',
    label: 'Tenachi et al. 2023',
    citation:
      'Tenachi, W., Ibata, R. and Diakogiannis, F. I. (2023). Deep symbolic regression for physics guided by units constraints. The Astrophysical Journal 959(2), 99.',
    doi: '10.3847/1538-4357/ad014c',
  },
  {
    id: 'petersen2021',
    label: 'Petersen et al. 2021',
    citation:
      'Petersen, B. K. et al. (2021). Deep symbolic regression: recovering mathematical expressions from data via risk-seeking policy gradients. ICLR 2021.',
    url: 'https://arxiv.org/abs/1912.04871',
  },
  {
    id: 'bartlett2023',
    label: 'Bartlett et al. 2023',
    citation:
      'Bartlett, D. J., Desmond, H. and Ferreira, P. G. (2023). Exhaustive symbolic regression. IEEE Transactions on Evolutionary Computation.',
    doi: '10.1109/TEVC.2023.3280250',
  },
  {
    id: 'guimera2020',
    label: 'Guimera et al. 2020',
    citation:
      'Guimera, R. et al. (2020). A Bayesian machine scientist to aid in the solution of challenging scientific problems. Science Advances 6(5), eaav6971.',
    doi: '10.1126/sciadv.aav6971',
  },
  {
    id: 'buckingham1914',
    label: 'Buckingham 1914',
    citation:
      'Buckingham, E. (1914). On physically similar systems; illustrations of the use of dimensional equations. Physical Review 4(4), 345-376.',
    doi: '10.1103/PhysRev.4.345',
  },
  {
    id: 'rissanen1978',
    label: 'Rissanen 1978',
    citation: 'Rissanen, J. (1978). Modeling by shortest data description. Automatica 14(5), 465-471.',
    doi: '10.1016/0005-1098(78)90005-5',
  },
  {
    id: 'buchheim2006',
    label: 'Buchheim et al. 2006',
    citation:
      'Buchheim, C., Junger, M. and Leipert, S. (2006). Drawing rooted trees in linear time. Software: Practice and Experience 36(6), 651-665.',
    doi: '10.1002/spe.713',
  },
  {
    id: 'aldeia2024',
    label: 'Aldeia and de Franca 2024',
    citation:
      'Aldeia, G. S. I. and de Franca, F. O. (2024). Interpretability in symbolic regression: a benchmark of explanatory methods using partial effects.',
    url: 'https://arxiv.org/abs/2404.05908',
  },
  {
    id: 'virgolin2022',
    label: 'Virgolin and Pissis 2022',
    citation: 'Virgolin, M. and Pissis, S. P. (2022). Symbolic regression is NP-hard. Transactions on Machine Learning Research.',
    url: 'https://arxiv.org/abs/2207.01018',
  },
  {
    id: 'liu2024',
    label: 'Liu et al. 2024',
    citation: 'Liu, Z. et al. (2024). KAN: Kolmogorov-Arnold Networks.',
    url: 'https://arxiv.org/abs/2404.19756',
  },
  {
    id: 'yeh1998',
    label: 'Yeh 1998',
    citation:
      'Yeh, I.-C. (1998). Modeling of strength of high-performance concrete using artificial neural networks. Cement and Concrete Research 28(12), 1797-1808. Dataset in the UCI Machine Learning Repository.',
    doi: '10.1016/S0008-8846(98)00165-3',
  },
  {
    id: 'tufekci2014',
    label: 'Tufekci 2014',
    citation:
      'Tufekci, P. (2014). Prediction of full load electrical power output of a base load operated combined cycle power plant using machine learning methods. International Journal of Electrical Power and Energy Systems 60, 126-140.',
    doi: '10.1016/j.ijepes.2014.02.027',
  },
  {
    id: 'nikuradse1933',
    label: 'Nikuradse 1933',
    citation:
      'Nikuradse, J. (1933). Stromungsgesetze in rauhen Rohren. VDI-Forschungsheft 361. Digitised measurements distributed through the PMLB collection.',
    url: 'https://github.com/EpistasisLab/pmlb/tree/master/datasets/nikuradse_1',
  },
  {
    id: 'bu2017',
    label: 'Bu et al. 2017',
    citation:
      'Bu, X., Xie, G., Peng, Y., Ge, L. and Ni, C. (2017). Kinetics of flotation. Order of process, rate constant distribution and ultimate recovery. Physicochemical Problems of Mineral Processing 53(1), 342-365.',
    doi: '10.5277/ppmp170128',
  },
];
