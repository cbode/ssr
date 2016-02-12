ssr
===

Subcanopy Solar Radiation Model

Author: Collin
Date: July, 2015


Citation: Subcanopy Solar Radiation model: Predicting solar radiation across a heavily vegetated landscape using LiDAR and GIS solar radiation models
CA Bode, MP Limm, ME Power, JC Finlay Remote Sensing of Environment 154, 387-397

What is SSR?
===
Solar radiation flux, irradiance, is a fundamental driver of almost all hydrological and biological processes.  Ecological models of these processes often require data at the watershed scale.  GIS-based solar models that predict insolation at the watershed scale take topographic shading into account, but do not account for vegetative shading.  Methods that quantify subcanopy insolation do so only at a single point.  Further, calibrating the subcanopy models requires significant field effort and knowledge of characteristics (leaf area index, mean leaf angle, clumping factor, etc.) of diverse species or assemblages of vegetation.  Upscaling from point values to watersheds is a significant source of uncertainty.
We propose an approach to modeling insolation that uses airborne LiDAR data to estimate canopy openness as a Light Penetration Index (LPI).  We couple LPI with the GRASS GIS r.sun solar model to produce the Subcanopy Solar Radiation model (SSR).  SSR accounts for both topographic shading and vegetative shading at a landscape scale. This approach allows prediction of light regimes at watershed scales with resolution that was previously possible only for local point measurements.  

Running SSR
===
Please see <a href="https://github.com/cbode/ssr/wiki">the documentation in the wiki</a>
