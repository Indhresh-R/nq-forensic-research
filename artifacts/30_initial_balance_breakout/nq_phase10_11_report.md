# Phase 10/11 — failed-acceptance response surface and timing

All 2D bins use Train-fixed quintiles. Cells are descriptive; no cell is a rule.

## 2D surface

| period     | direction             | exc_q   | rej_q   |   n |     mfe60 |     mae60 |        net60 |
|:-----------|:----------------------|:--------|:--------|----:|----------:|----------:|-------------:|
| Inner      | downside_failure_long | Q1      | Q1      |   2 | 0.36411   | 0.719222  | -0.355112    |
| Inner      | downside_failure_long | Q1      | Q2      |   1 | 0.264569  | 0.0431235 |  0.221445    |
| Inner      | downside_failure_long | Q1      | Q3      |   2 | 0.2536    | 0.482133  | -0.228533    |
| Inner      | downside_failure_long | Q1      | Q4      |   3 | 0.334301  | 0.266163  |  0.0681375   |
| Inner      | downside_failure_long | Q1      | Q5      |  20 | 0.286073  | 0.37522   | -0.0891466   |
| Inner      | downside_failure_long | Q2      | Q1      |   2 | 0.157448  | 1.38695   | -1.2295      |
| Inner      | downside_failure_long | Q2      | Q2      |   4 | 0.157704  | 0.347613  | -0.189909    |
| Inner      | downside_failure_long | Q2      | Q3      |   4 | 0.0807637 | 0.59018   | -0.509416    |
| Inner      | downside_failure_long | Q2      | Q4      |  12 | 0.372904  | 0.274822  |  0.098082    |
| Inner      | downside_failure_long | Q2      | Q5      |  20 | 0.24781   | 0.886087  | -0.638277    |
| Inner      | downside_failure_long | Q3      | Q1      |   3 | 0.131588  | 0.784167  | -0.652579    |
| Inner      | downside_failure_long | Q3      | Q2      |   8 | 0.242203  | 0.439657  | -0.197453    |
| Inner      | downside_failure_long | Q3      | Q3      |  11 | 0.19345   | 0.360155  | -0.166705    |
| Inner      | downside_failure_long | Q3      | Q4      |  15 | 0.357843  | 0.296506  |  0.0613365   |
| Inner      | downside_failure_long | Q3      | Q5      |  10 | 0.358321  | 0.257314  |  0.101007    |
| Inner      | downside_failure_long | Q4      | Q1      |   3 | 0.224671  | 0.254801  | -0.0301299   |
| Inner      | downside_failure_long | Q4      | Q2      |  13 | 0.389894  | 0.28754   |  0.102354    |
| Inner      | downside_failure_long | Q4      | Q3      |  14 | 0.369458  | 0.480716  | -0.111258    |
| Inner      | downside_failure_long | Q4      | Q4      |   8 | 0.595914  | 0.372682  |  0.223231    |
| Inner      | downside_failure_long | Q4      | Q5      |   3 | 0.385018  | 0.434795  | -0.0497765   |
| Inner      | downside_failure_long | Q5      | Q1      |  22 | 0.363275  | 0.456556  | -0.0932807   |
| Inner      | downside_failure_long | Q5      | Q2      |  22 | 0.30009   | 0.512371  | -0.212281    |
| Inner      | downside_failure_long | Q5      | Q3      |  12 | 0.288231  | 0.299834  | -0.0116023   |
| Inner      | downside_failure_long | Q5      | Q4      |   1 | 0.107011  | 0.98893   | -0.881919    |
| Inner      | upside_failure_short  | Q1      | Q1      |   3 | 0.203692  | 0.28363   | -0.0799378   |
| Inner      | upside_failure_short  | Q1      | Q2      |   6 | 0.14579   | 0.172947  | -0.0271566   |
| Inner      | upside_failure_short  | Q1      | Q3      |   8 | 0.128056  | 0.244876  | -0.11682     |
| Inner      | upside_failure_short  | Q1      | Q4      |  16 | 0.266505  | 0.204586  |  0.0619186   |
| Inner      | upside_failure_short  | Q1      | Q5      |  42 | 0.219551  | 0.355758  | -0.136206    |
| Inner      | upside_failure_short  | Q2      | Q1      |  12 | 0.201385  | 0.190591  |  0.0107937   |
| Inner      | upside_failure_short  | Q2      | Q2      |  13 | 0.241904  | 0.344558  | -0.102654    |
| Inner      | upside_failure_short  | Q2      | Q3      |  17 | 0.31485   | 0.321293  | -0.00644283  |
| Inner      | upside_failure_short  | Q2      | Q4      |  14 | 0.221922  | 0.268321  | -0.046399    |
| Inner      | upside_failure_short  | Q2      | Q5      |  19 | 0.320504  | 0.349592  | -0.0290885   |
| Inner      | upside_failure_short  | Q3      | Q1      |  13 | 0.248367  | 0.267958  | -0.019591    |
| Inner      | upside_failure_short  | Q3      | Q2      |  11 | 0.317444  | 0.294395  |  0.0230494   |
| Inner      | upside_failure_short  | Q3      | Q3      |  10 | 0.266123  | 0.316342  | -0.0502194   |
| Inner      | upside_failure_short  | Q3      | Q4      |  15 | 0.244355  | 0.270732  | -0.0263766   |
| Inner      | upside_failure_short  | Q3      | Q5      |   3 | 0.112691  | 0.803101  | -0.690411    |
| Inner      | upside_failure_short  | Q4      | Q1      |   9 | 0.277587  | 0.264243  |  0.0133444   |
| Inner      | upside_failure_short  | Q4      | Q2      |   8 | 0.399782  | 0.305486  |  0.0942965   |
| Inner      | upside_failure_short  | Q4      | Q3      |   8 | 0.256258  | 0.271791  | -0.0155323   |
| Inner      | upside_failure_short  | Q4      | Q4      |   4 | 0.77197   | 0.180628  |  0.591342    |
| Inner      | upside_failure_short  | Q4      | Q5      |   3 | 0.648807  | 0.282326  |  0.366481    |
| Inner      | upside_failure_short  | Q5      | Q1      |  11 | 0.318831  | 0.506377  | -0.187546    |
| Inner      | upside_failure_short  | Q5      | Q2      |  13 | 0.400713  | 0.285582  |  0.115131    |
| Inner      | upside_failure_short  | Q5      | Q3      |  16 | 0.419497  | 0.406032  |  0.0134654   |
| Inner      | upside_failure_short  | Q5      | Q4      |   8 | 0.465736  | 0.379636  |  0.0861      |
| Inner      | upside_failure_short  | Q5      | Q5      |   1 | 1.73741   | 0.122302  |  1.61511     |
| OOS        | downside_failure_long | Q1      | Q3      |   1 | 0.259977  | 0.0416667 |  0.21831     |
| OOS        | downside_failure_long | Q1      | Q4      |   3 | 0.352623  | 0.28892   |  0.0637032   |
| OOS        | downside_failure_long | Q1      | Q5      |  13 | 0.175687  | 0.447239  | -0.271552    |
| OOS        | downside_failure_long | Q2      | Q1      |   3 | 0.482074  | 0.391006  |  0.0910685   |
| OOS        | downside_failure_long | Q2      | Q2      |   4 | 0.139695  | 0.184917  | -0.0452223   |
| OOS        | downside_failure_long | Q2      | Q3      |   4 | 0.379196  | 0.3319    |  0.0472954   |
| OOS        | downside_failure_long | Q2      | Q4      |   5 | 0.469754  | 0.147127  |  0.322627    |
| OOS        | downside_failure_long | Q2      | Q5      |   7 | 0.254089  | 0.409488  | -0.155399    |
| OOS        | downside_failure_long | Q3      | Q1      |   3 | 0.347074  | 0.395878  | -0.0488042   |
| OOS        | downside_failure_long | Q3      | Q2      |   5 | 0.109434  | 0.597146  | -0.487712    |
| OOS        | downside_failure_long | Q3      | Q3      |   4 | 0.335829  | 0.40416   | -0.0683315   |
| OOS        | downside_failure_long | Q3      | Q4      |   6 | 0.233782  | 0.377901  | -0.144119    |
| OOS        | downside_failure_long | Q3      | Q5      |   7 | 0.397157  | 0.373492  |  0.0236645   |
| OOS        | downside_failure_long | Q4      | Q1      |   7 | 0.27227   | 0.366917  | -0.094647    |
| OOS        | downside_failure_long | Q4      | Q2      |   1 | 0.506143  | 0.044226  |  0.461916    |
| OOS        | downside_failure_long | Q4      | Q3      |  11 | 0.283346  | 0.399154  | -0.115808    |
| OOS        | downside_failure_long | Q4      | Q4      |   5 | 0.343542  | 0.423803  | -0.0802616   |
| OOS        | downside_failure_long | Q4      | Q5      |   3 | 0.833713  | 0.370253  |  0.46346     |
| OOS        | downside_failure_long | Q5      | Q1      |   4 | 0.408998  | 0.485929  | -0.0769313   |
| OOS        | downside_failure_long | Q5      | Q2      |  11 | 0.320218  | 0.276479  |  0.0437385   |
| OOS        | downside_failure_long | Q5      | Q3      |   5 | 0.282547  | 0.442934  | -0.160386    |
| OOS        | downside_failure_long | Q5      | Q4      |   3 | 0.655207  | 0.338291  |  0.316916    |
| OOS        | downside_failure_long | Q5      | Q5      |   1 | 0.171296  | 1.02315   | -0.851852    |
| OOS        | upside_failure_short  | Q1      | Q1      |   3 | 0.164662  | 0.365808  | -0.201146    |
| OOS        | upside_failure_short  | Q1      | Q2      |   4 | 0.249109  | 0.17057   |  0.0785392   |
| OOS        | upside_failure_short  | Q1      | Q3      |   7 | 0.141575  | 0.233541  | -0.0919651   |
| OOS        | upside_failure_short  | Q1      | Q4      |  18 | 0.207905  | 0.227972  | -0.0200677   |
| OOS        | upside_failure_short  | Q1      | Q5      |  29 | 0.246894  | 0.265365  | -0.0184708   |
| OOS        | upside_failure_short  | Q2      | Q1      |   3 | 0.0957846 | 0.158807  | -0.0630225   |
| OOS        | upside_failure_short  | Q2      | Q2      |   6 | 0.317751  | 0.192426  |  0.125325    |
| OOS        | upside_failure_short  | Q2      | Q3      |   9 | 0.401256  | 0.150235  |  0.25102     |
| OOS        | upside_failure_short  | Q2      | Q4      |  10 | 0.26077   | 0.247452  |  0.0133187   |
| OOS        | upside_failure_short  | Q2      | Q5      |  11 | 0.25719   | 0.517173  | -0.259983    |
| OOS        | upside_failure_short  | Q3      | Q1      |   3 | 0.327112  | 0.28966   |  0.0374522   |
| OOS        | upside_failure_short  | Q3      | Q2      |   3 | 0.289247  | 0.242983  |  0.0462642   |
| OOS        | upside_failure_short  | Q3      | Q3      |   4 | 0.154849  | 1.21424   | -1.05939     |
| OOS        | upside_failure_short  | Q3      | Q4      |   6 | 0.196109  | 0.330891  | -0.134782    |
| OOS        | upside_failure_short  | Q3      | Q5      |   9 | 0.597313  | 0.264431  |  0.332882    |
| OOS        | upside_failure_short  | Q4      | Q1      |   4 | 0.308032  | 0.246527  |  0.0615053   |
| OOS        | upside_failure_short  | Q4      | Q2      |   6 | 0.327578  | 0.424573  | -0.0969954   |
| OOS        | upside_failure_short  | Q4      | Q3      |   6 | 0.244054  | 0.46018   | -0.216126    |
| OOS        | upside_failure_short  | Q4      | Q4      |   8 | 0.322933  | 0.25744   |  0.0654937   |
| OOS        | upside_failure_short  | Q4      | Q5      |   1 | 0.385269  | 0.61898   | -0.233711    |
| OOS        | upside_failure_short  | Q5      | Q1      |   3 | 0.296799  | 0.367632  | -0.0708333   |
| OOS        | upside_failure_short  | Q5      | Q2      |   3 | 0.405973  | 0.150317  |  0.255656    |
| OOS        | upside_failure_short  | Q5      | Q3      |   4 | 0.367034  | 0.608865  | -0.241831    |
| OOS        | upside_failure_short  | Q5      | Q4      |   3 | 1.01101   | 0.19729   |  0.813722    |
| Train      | downside_failure_long | Q1      | Q1      |  10 | 0.188848  | 0.289939  | -0.101092    |
| Train      | downside_failure_long | Q1      | Q2      |   2 | 0.0923792 | 0.28081   | -0.188431    |
| Train      | downside_failure_long | Q1      | Q3      |   7 | 0.184931  | 0.211348  | -0.0264177   |
| Train      | downside_failure_long | Q1      | Q4      |  14 | 0.249214  | 0.365446  | -0.116232    |
| Train      | downside_failure_long | Q1      | Q5      |  36 | 0.229272  | 0.388833  | -0.159561    |
| Train      | downside_failure_long | Q2      | Q1      |  13 | 0.223206  | 0.472653  | -0.249448    |
| Train      | downside_failure_long | Q2      | Q2      |   8 | 0.281758  | 0.440093  | -0.158335    |
| Train      | downside_failure_long | Q2      | Q3      |  17 | 0.225772  | 0.498355  | -0.272583    |
| Train      | downside_failure_long | Q2      | Q4      |  26 | 0.314517  | 0.310524  |  0.00399291  |
| Train      | downside_failure_long | Q2      | Q5      |  24 | 0.238958  | 0.559352  | -0.320393    |
| Train      | downside_failure_long | Q3      | Q1      |  11 | 0.232816  | 0.371904  | -0.139088    |
| Train      | downside_failure_long | Q3      | Q2      |  15 | 0.24761   | 0.463348  | -0.215738    |
| Train      | downside_failure_long | Q3      | Q3      |  16 | 0.299069  | 0.370812  | -0.0717429   |
| Train      | downside_failure_long | Q3      | Q4      |  28 | 0.303753  | 0.396964  | -0.0932108   |
| Train      | downside_failure_long | Q3      | Q5      |  15 | 0.407997  | 0.286643  |  0.121355    |
| Train      | downside_failure_long | Q4      | Q1      |  25 | 0.34105   | 0.265535  |  0.0755147   |
| Train      | downside_failure_long | Q4      | Q2      |  22 | 0.305233  | 0.373109  | -0.0678761   |
| Train      | downside_failure_long | Q4      | Q3      |  30 | 0.387999  | 0.424583  | -0.0365831   |
| Train      | downside_failure_long | Q4      | Q4      |  22 | 0.417978  | 0.368278  |  0.0497005   |
| Train      | downside_failure_long | Q4      | Q5      |   6 | 0.498615  | 0.29271   |  0.205905    |
| Train      | downside_failure_long | Q5      | Q1      |  41 | 0.40673   | 0.365646  |  0.0410846   |
| Train      | downside_failure_long | Q5      | Q2      |  46 | 0.350881  | 0.360523  | -0.00964235  |
| Train      | downside_failure_long | Q5      | Q3      |  21 | 0.513292  | 0.47744   |  0.0358518   |
| Train      | downside_failure_long | Q5      | Q4      |  13 | 0.645932  | 0.609783  |  0.0361488   |
| Train      | upside_failure_short  | Q1      | Q1      |  17 | 0.233138  | 0.26901   | -0.0358717   |
| Train      | upside_failure_short  | Q1      | Q2      |   9 | 0.133045  | 0.429615  | -0.29657     |
| Train      | upside_failure_short  | Q1      | Q3      |  13 | 0.141578  | 0.312421  | -0.170843    |
| Train      | upside_failure_short  | Q1      | Q4      |  28 | 0.190078  | 0.266993  | -0.0769154   |
| Train      | upside_failure_short  | Q1      | Q5      |  67 | 0.199144  | 0.339221  | -0.140076    |
| Train      | upside_failure_short  | Q2      | Q1      |  16 | 0.206447  | 0.221427  | -0.0149807   |
| Train      | upside_failure_short  | Q2      | Q2      |  18 | 0.266648  | 0.219703  |  0.0469453   |
| Train      | upside_failure_short  | Q2      | Q3      |  21 | 0.380604  | 0.328947  |  0.0516566   |
| Train      | upside_failure_short  | Q2      | Q4      |  26 | 0.218829  | 0.351809  | -0.132979    |
| Train      | upside_failure_short  | Q2      | Q5      |  33 | 0.276813  | 0.304782  | -0.0279689   |
| Train      | upside_failure_short  | Q3      | Q1      |  18 | 0.440175  | 0.218385  |  0.22179     |
| Train      | upside_failure_short  | Q3      | Q2      |  30 | 0.30898   | 0.219161  |  0.0898193   |
| Train      | upside_failure_short  | Q3      | Q3      |  34 | 0.234478  | 0.334541  | -0.100063    |
| Train      | upside_failure_short  | Q3      | Q4      |  23 | 0.321941  | 0.372804  | -0.0508632   |
| Train      | upside_failure_short  | Q3      | Q5      |  13 | 0.32018   | 0.34392   | -0.0237405   |
| Train      | upside_failure_short  | Q4      | Q1      |  26 | 0.292471  | 0.35225   | -0.0597794   |
| Train      | upside_failure_short  | Q4      | Q2      |  24 | 0.39865   | 0.29696   |  0.10169     |
| Train      | upside_failure_short  | Q4      | Q3      |  26 | 0.396847  | 0.254381  |  0.142466    |
| Train      | upside_failure_short  | Q4      | Q4      |  17 | 0.433317  | 0.278992  |  0.154325    |
| Train      | upside_failure_short  | Q4      | Q5      |   4 | 0.884271  | 0.120902  |  0.763368    |
| Train      | upside_failure_short  | Q5      | Q1      |  26 | 0.37012   | 0.322676  |  0.0474434   |
| Train      | upside_failure_short  | Q5      | Q2      |  28 | 0.443453  | 0.296947  |  0.146506    |
| Train      | upside_failure_short  | Q5      | Q3      |  18 | 0.46727   | 0.265398  |  0.201872    |
| Train      | upside_failure_short  | Q5      | Q4      |   6 | 0.13967   | 0.557798  | -0.418128    |
| Train      | upside_failure_short  | Q5      | Q5      |   4 | 1.28046   | 0.197378  |  1.08308     |
| Validation | downside_failure_long | Q1      | Q1      |   2 | 0.253578  | 0.221524  |  0.0320547   |
| Validation | downside_failure_long | Q1      | Q2      |   1 | 0.368889  | 0.0288889 |  0.34        |
| Validation | downside_failure_long | Q1      | Q3      |   4 | 0.351034  | 0.268913  |  0.0821209   |
| Validation | downside_failure_long | Q1      | Q4      |   9 | 0.159146  | 0.312955  | -0.153808    |
| Validation | downside_failure_long | Q1      | Q5      |  30 | 0.223267  | 0.325161  | -0.101894    |
| Validation | downside_failure_long | Q2      | Q1      |   4 | 0.238814  | 0.238145  |  0.000669278 |
| Validation | downside_failure_long | Q2      | Q2      |   3 | 0.26213   | 0.25194   |  0.0101904   |
| Validation | downside_failure_long | Q2      | Q3      |  21 | 0.293802  | 0.234424  |  0.0593786   |
| Validation | downside_failure_long | Q2      | Q4      |  12 | 0.333735  | 0.274191  |  0.0595445   |
| Validation | downside_failure_long | Q2      | Q5      |  15 | 0.235239  | 0.539997  | -0.304758    |
| Validation | downside_failure_long | Q3      | Q1      |   5 | 0.256888  | 0.644387  | -0.387499    |
| Validation | downside_failure_long | Q3      | Q2      |  12 | 0.348719  | 0.275685  |  0.0730347   |
| Validation | downside_failure_long | Q3      | Q3      |   8 | 0.191078  | 0.372609  | -0.181531    |
| Validation | downside_failure_long | Q3      | Q4      |  18 | 0.317546  | 0.423349  | -0.105803    |
| Validation | downside_failure_long | Q3      | Q5      |   8 | 0.228337  | 0.653765  | -0.425428    |
| Validation | downside_failure_long | Q4      | Q1      |  10 | 0.331459  | 0.358433  | -0.0269735   |
| Validation | downside_failure_long | Q4      | Q2      |  13 | 0.276449  | 0.239661  |  0.0367883   |
| Validation | downside_failure_long | Q4      | Q3      |  11 | 0.44371   | 0.21107   |  0.232639    |
| Validation | downside_failure_long | Q4      | Q4      |  12 | 0.449668  | 0.343439  |  0.10623     |
| Validation | downside_failure_long | Q4      | Q5      |   1 | 0.190291  | 0.271845  | -0.0815534   |
| Validation | downside_failure_long | Q5      | Q1      |  18 | 0.311841  | 0.306327  |  0.00551376  |
| Validation | downside_failure_long | Q5      | Q2      |  22 | 0.379998  | 0.30205   |  0.0779482   |
| Validation | downside_failure_long | Q5      | Q3      |  11 | 0.330455  | 0.371794  | -0.041339    |
| Validation | downside_failure_long | Q5      | Q4      |   6 | 0.195211  | 0.501144  | -0.305934    |
| Validation | downside_failure_long | Q5      | Q5      |   1 | 0.710769  | 3.49846   | -2.78769     |
| Validation | upside_failure_short  | Q1      | Q1      |   5 | 0.214553  | 0.305574  | -0.091021    |
| Validation | upside_failure_short  | Q1      | Q2      |   5 | 0.383873  | 0.208035  |  0.175838    |
| Validation | upside_failure_short  | Q1      | Q3      |   4 | 0.241553  | 0.189486  |  0.0520669   |
| Validation | upside_failure_short  | Q1      | Q4      |  12 | 0.183128  | 0.211408  | -0.0282806   |
| Validation | upside_failure_short  | Q1      | Q5      |  40 | 0.225711  | 0.345982  | -0.120271    |
| Validation | upside_failure_short  | Q2      | Q1      |  10 | 0.493065  | 0.23586   |  0.257206    |
| Validation | upside_failure_short  | Q2      | Q2      |  13 | 0.222755  | 0.233459  | -0.0107038   |
| Validation | upside_failure_short  | Q2      | Q3      |  19 | 0.264114  | 0.288662  | -0.0245476   |
| Validation | upside_failure_short  | Q2      | Q4      |  13 | 0.215175  | 0.36557   | -0.150395    |
| Validation | upside_failure_short  | Q2      | Q5      |  15 | 0.304571  | 0.425502  | -0.120931    |
| Validation | upside_failure_short  | Q3      | Q1      |   3 | 0.694406  | 0.321505  |  0.372901    |
| Validation | upside_failure_short  | Q3      | Q2      |  12 | 0.161961  | 0.414649  | -0.252687    |
| Validation | upside_failure_short  | Q3      | Q3      |  16 | 0.27212   | 0.326248  | -0.054128    |
| Validation | upside_failure_short  | Q3      | Q4      |  12 | 0.379722  | 0.2685    |  0.111222    |
| Validation | upside_failure_short  | Q3      | Q5      |   9 | 0.400902  | 0.325005  |  0.0758964   |
| Validation | upside_failure_short  | Q4      | Q1      |   6 | 0.356873  | 0.23906   |  0.117813    |
| Validation | upside_failure_short  | Q4      | Q2      |   8 | 0.420191  | 0.421603  | -0.00141236  |
| Validation | upside_failure_short  | Q4      | Q3      |  13 | 0.351032  | 0.304266  |  0.0467659   |
| Validation | upside_failure_short  | Q4      | Q4      |  12 | 0.262723  | 0.441141  | -0.178418    |
| Validation | upside_failure_short  | Q4      | Q5      |   2 | 0.216817  | 0.907975  | -0.691159    |
| Validation | upside_failure_short  | Q5      | Q1      |  12 | 0.48184   | 0.295676  |  0.186164    |
| Validation | upside_failure_short  | Q5      | Q2      |  14 | 0.450611  | 0.288127  |  0.162484    |
| Validation | upside_failure_short  | Q5      | Q3      |  14 | 0.571223  | 0.340418  |  0.230805    |
| Validation | upside_failure_short  | Q5      | Q4      |   2 | 0.306466  | 0.258488  |  0.0479771   |

## Reversal timing

| period     | direction             |   horizon_min |   n |       mfe |       mae |          net |
|:-----------|:----------------------|--------------:|----:|----------:|----------:|-------------:|
| Inner      | downside_failure_long |             5 | 215 | 0.0842036 | 0.121741  | -0.037537    |
| Inner      | downside_failure_long |            10 | 215 | 0.1259    | 0.173156  | -0.047256    |
| Inner      | downside_failure_long |            15 | 215 | 0.151857  | 0.216379  | -0.0645217   |
| Inner      | downside_failure_long |            30 | 215 | 0.217999  | 0.28953   | -0.0715315   |
| Inner      | downside_failure_long |            60 | 215 | 0.313175  | 0.44915   | -0.135975    |
| Inner      | upside_failure_short  |             5 | 283 | 0.0961568 | 0.0930013 |  0.00315546  |
| Inner      | upside_failure_short  |            10 | 283 | 0.135492  | 0.134674  |  0.000818313 |
| Inner      | upside_failure_short  |            15 | 283 | 0.165469  | 0.163897  |  0.0015722   |
| Inner      | upside_failure_short  |            30 | 283 | 0.21739   | 0.230852  | -0.0134619   |
| Inner      | upside_failure_short  |            60 | 283 | 0.293865  | 0.312897  | -0.0190325   |
| OOS        | downside_failure_long |             5 | 116 | 0.108394  | 0.125422  | -0.0170276   |
| OOS        | downside_failure_long |            10 | 116 | 0.141591  | 0.179614  | -0.0380222   |
| OOS        | downside_failure_long |            15 | 116 | 0.165393  | 0.210354  | -0.0449612   |
| OOS        | downside_failure_long |            30 | 116 | 0.237162  | 0.283505  | -0.0463424   |
| OOS        | downside_failure_long |            60 | 116 | 0.317424  | 0.376789  | -0.0593649   |
| OOS        | upside_failure_short  |             5 | 163 | 0.117033  | 0.0816261 |  0.0354065   |
| OOS        | upside_failure_short  |            10 | 163 | 0.157777  | 0.128969  |  0.0288077   |
| OOS        | upside_failure_short  |            15 | 163 | 0.184258  | 0.167164  |  0.0170932   |
| OOS        | upside_failure_short  |            30 | 163 | 0.241544  | 0.239432  |  0.00211206  |
| OOS        | upside_failure_short  |            60 | 163 | 0.293783  | 0.311255  | -0.017471    |
| Train      | downside_failure_long |             5 | 468 | 0.0915915 | 0.113265  | -0.0216735   |
| Train      | downside_failure_long |            10 | 468 | 0.128667  | 0.164771  | -0.0361038   |
| Train      | downside_failure_long |            15 | 468 | 0.161432  | 0.203212  | -0.0417808   |
| Train      | downside_failure_long |            30 | 468 | 0.233496  | 0.289851  | -0.056355    |
| Train      | downside_failure_long |            60 | 468 | 0.330691  | 0.391133  | -0.0604424   |
| Train      | upside_failure_short  |             5 | 545 | 0.0871799 | 0.0916708 | -0.00449098  |
| Train      | upside_failure_short  |            10 | 545 | 0.124386  | 0.127899  | -0.00351329  |
| Train      | upside_failure_short  |            15 | 545 | 0.152135  | 0.156145  | -0.00401042  |
| Train      | upside_failure_short  |            30 | 545 | 0.220634  | 0.216539  |  0.00409573  |
| Train      | upside_failure_short  |            60 | 545 | 0.30848   | 0.302723  |  0.00575703  |
| Validation | downside_failure_long |             5 | 257 | 0.0924719 | 0.104582  | -0.0121097   |
| Validation | downside_failure_long |            10 | 257 | 0.130395  | 0.143057  | -0.0126617   |
| Validation | downside_failure_long |            15 | 257 | 0.160268  | 0.178342  | -0.0180748   |
| Validation | downside_failure_long |            30 | 257 | 0.226611  | 0.249215  | -0.0226044   |
| Validation | downside_failure_long |            60 | 257 | 0.300628  | 0.352805  | -0.0521771   |
| Validation | upside_failure_short  |             5 | 271 | 0.106587  | 0.0991369 |  0.00745016  |
| Validation | upside_failure_short  |            10 | 271 | 0.148254  | 0.13975   |  0.0085034   |
| Validation | upside_failure_short  |            15 | 271 | 0.174778  | 0.171188  |  0.00358948  |
| Validation | upside_failure_short  |            30 | 271 | 0.231595  | 0.241691  | -0.0100953   |
| Validation | upside_failure_short  |            60 | 271 | 0.318426  | 0.323836  | -0.00541009  |