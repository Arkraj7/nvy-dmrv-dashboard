// const path = window.location.pathname;
// const isIndexPage = path.endsWith("index.html") || path.endsWith("/") || path === "";
// const isReportPage = path.endsWith("report.html");

// let chart;
// let areaUnit = "m2";
// let adWatched = false;
// let selectedUnit = "m2";
// let calculatedResults = null;
// let category = "green-tab";
// let inputData = ["0", "0", "0", "0"];

// // const placeholders = {
// //     "green-tab": ["co2", "biodiversity", "cooling", "air", "stormwater", "branding", "cars", "households", "credits"],
// //     "energy-tab": ["annualEnergy", "energyCost", "renewableShare", "energyIntensity", "energySavings", "ghg", ],
// //     "water-tab": ["totalUse", "netConsumption", "reusePercent", "stormInfiltration", "waterIntensity", "hydroBalance"],
// //     "waste-tab": ["totalWaste", "recycleRate", "landfillRate", "energyPotential", "wasteIntensity", "reductionPercent"]
// //   };

// function isCalculatorPage() {
//   return window.location.pathname.endsWith('calculator.html');
// }

// const inputHeaders = {
//   "green-tab": ["Number of Trees", "Number of Species", "Area", "Project Duration"],
//   "energy-tab": ["Electricity Consumption", "Renewable Electricity Used", "Power Rating of Equipment", "Operating Hours per Day"],
//   "water-tab": ["Water Withdrawal", "Water Discharged", "Water Reused", "Site Area"],
//   "waste-tab": ["Hazardous Waste", "Non-Hazardous Waste", "Waste Recycled", "Waste Sent to Landfill"]
// }

// const inputUnits = {
//   "green-tab": ["", "", "m²", "years"],
//   "energy-tab": ["kWh/year", "kWh/year", "kW", "hours/day"],
//   "water-tab": ["Litres/year", "Litres/year", "Litres/year", "m²"],
//   "waste-tab": ["kg/year", "kg/year", "kg", "m²"]
// }

// // const tooltipContent = {
// //   "green-tab": ["Estimated carbon captured annually by the trees. Removes harmful carbon dioxide from the atmosphere each year, helping slow climate change.", "Relative biodiversity score based on species richness per area. Shows how effectively the green space can support diverse plant and animal life.", "Cooling potential created by green space. Reduces surrounding temperatures naturally, improving comfort and lowering heat stress.", "Amount of PM2.5 removed by trees annually. Filters pollutants like PM2.5 from the air, providing cleaner and healthier air to breathe.", "Rainwater intercepted by green surfaces annually. Absorbs rainfall and reduces flooding risk while improving groundwater replenishment.", "A maturity indicator combining age, species, and trees. Reflects the environmental leadership and maturity of your green initiative.", "Equivalent number of average petrol cars' annual CO₂ emissions avoided.", "Number of average households' annual electricity use offset by saved emissions.", "Approximate number of 1-tonne CO₂ credits represented."],
// //   "energy-tab": ["Total energy consumed annually. Represents the total energy consumed annually, helping track operational efficiency.", "Estimated cost of consumed electricity. Shows the annual financial cost of electricity consumption to highlight savings opportunities.", "Percentage share of renewable energy. Indicates how much of your total energy comes from clean, renewable sources.", "Energy needed per unit of user-defined output. Reveals the amount of energy required per unit of output, showing operational efficiency.", "Reduction in energy use relative to baseline. Shows how much energy you have saved compared to the baseline, demonstrating improvement.", "Emissions caused by electricity usage. Quantifies the climate-impacting emissions generated from electricity use.", "Equivalent months of an average household's electricity supplied by saved energy.", "Volume of petrol whose combustion equals the energy saved.", "Energy savings expressed in gigajoules."],
// //   "water-tab": ["Total water withdrawn from all sources. Measures the total water withdrawn from all sources for your operations.", "Water consumed after reuse and discharge. Shows the actual water consumed after subtracting reused and discharged water.", "Percentage of withdrawn water reused. Indicates how effectively your system recycles water, reducing freshwater demand.", "Estimated annual stormwater infiltration. Estimates how much rainwater your site can naturally filter back into the ground.", "Water consumption per output unit. Shows how much water is consumed per unit of output, helping identify efficiency gains.", "Water retained or released by site. Indicates whether your site retains or releases water overall.", "Number of typical household showers that volume of water could supply.", "Months of water supply for one household (basic use) provided.", "Number of standard Olympic pools worth of water saved."],
// //   "waste-tab": ["Combined hazardous and non-hazardous waste. Represents the combined hazardous and non-hazardous waste produced annually.", "Percentage of waste recycled. Shows the percentage of waste diverted from disposal through recycling.", "Percentage of waste landfilled. Indicates how much waste ends up in landfills, supporting zero-waste goals.", "Potential energy from recoverable waste. Shows how much usable energy can be recovered from organic waste.", "Waste generated per output unit. Measures waste generated per unit of output, highlighting efficiency improvements.", "Reduction in waste compared to baseline. Shows how effectively waste has been reduced compared to your baseline levels.", "Number of standard 10-tonne truckloads reduced.", "Approximate trees' worth of carbon avoided by diverting waste.", "Potential electricity from waste-to-energy for organic fraction."]
// // }

// let tooltipContent = [];

// let labels = [];
// let units = [];
// let ids = [];



// const infoIcons = document.querySelectorAll(".branding-info");
// const tooltips = document.querySelectorAll(".branding-tooltip");

// infoIcons.forEach((infoIcon, index) => {
//   const tooltip = tooltips[index];
//   infoIcon.addEventListener('click', (e) => {
//     tooltips.forEach(t => {
//       if (t !== tooltip) t.style.display = 'none';
//     });
    
//     tooltip.style.display = tooltip.style.display === 'block' ? 'none' : 'block';
//     e.stopPropagation();
//   });
// });

// document.addEventListener('click', (e) => {
//   infoIcons.forEach((infoIcon, index) => {
//     const tooltip = tooltips[index];
//     if (!infoIcon.contains(e.target) && !tooltip.contains(e.target)) {
//       tooltip.style.display = 'none';
//     }
//   });
// });




// document.addEventListener("DOMContentLoaded", () => {
//   const AC_TO_M2 = 4046.86;

//   function displayFromM2(m2, unit) {
//     return unit === "ac" ? m2 / AC_TO_M2 : m2;
//   }

//   function m2FromDisplay(displayValue, unit) {
//     return unit === "ac" ? displayValue * AC_TO_M2 : displayValue;
//   }


//   function initAreaDivValues() {
//     document.querySelectorAll(".area-div").forEach(areaDiv => {
//       const numInput = areaDiv.querySelector(".number-with-unit input[type='number']");
//       if (!numInput) return;
//       const checkedUnit = areaDiv.querySelector("input[type='radio']:checked")?.value || "m2";
//       const displayVal = parseFloat(numInput.value) || 0;
//       numInput.dataset.m2 = m2FromDisplay(displayVal, checkedUnit);
//     });
//   }


//   function updateAreaDiv(areaDiv, chosenUnit) {
//     const numInput = areaDiv.querySelector(".number-with-unit input[type='number']");
//     const unitSpan = areaDiv.querySelector(".number-with-unit span");
//     const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");

//     if (!numInput || !unitSpan) return;

//     const m2 = parseFloat(numInput.dataset.m2) || 0;
//     const newDisplay = displayFromM2(m2, chosenUnit);

//     numInput.value = Number(newDisplay.toFixed(chosenUnit === "ac" ? 4 : 2));
//     unitSpan.textContent = chosenUnit === "ac" ? "ac" : "m²";

//     if (rangeInput) {
//       rangeInput.max = chosenUnit === "ac" ? 50 : 200000;
//       rangeInput.value = numInput.value;
//     }

//     updateAllSliderFills?.();
//     if (typeof adWatched !== "undefined" && adWatched) calculate?.();
//   }


//   document.addEventListener("input", e => {
//     if (!e.target.matches(".area-div .number-with-unit input[type='number']")) return;

//     const numInput = e.target;
//     const areaDiv = numInput.closest(".area-div");
//     const curUnit = areaDiv.querySelector("input[type='radio']:checked")?.value || "m2";
//     const displayVal = parseFloat(numInput.value) || 0;

//     numInput.dataset.m2 = m2FromDisplay(displayVal, curUnit);

//     const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");
//     if (rangeInput) rangeInput.value = displayVal;

//     updateAllSliderFills?.();
//     if (typeof adWatched !== "undefined" && adWatched) calculate?.();
//   });


//   document.addEventListener("change", e => {
//     if (!e.target.matches(".area-div input[type='radio']")) return;
//     const radio = e.target;
//     const areaDiv = radio.closest(".area-div");
//     const chosenUnit = radio.value;
//     updateAreaDiv(areaDiv, chosenUnit);
//   });


//   initAreaDivValues();


//   const generateBtn = document.getElementById("generateAgain") || document.getElementById("generateAgainBtn");
//   if (generateBtn) {
//     generateBtn.addEventListener("click", () => {
//       console.log("Generate Again clicked — reinitializing area inputs");
//       requestAnimationFrame(initAreaDivValues);
//     });
//   } else {
//     console.log("generateAgain button not found during DOMContentLoaded");
//   }
// });






// function updateAllSliderFills() {
//   console.log("update slider fills");
//   document.querySelectorAll('input[type="range"]').forEach(slider => {
//     const min = parseFloat(slider.min) || 0;
//     const max = parseFloat(slider.max) || 100;
//     const val = parseFloat(slider.value);
//     const percent = ((val - min) / (max - min)) * 100;

//     slider.style.background = `linear-gradient(to right, #7acb8a 0%, #7acb8a ${percent}%, #f0f0f0 ${percent}%, #f0f0f0 100%)`;
//   });
// }

// function validateNonNegative(input) {
//   if (input.value.startsWith("-")) {
//     input.value = input.value.replace("-", "");
//   }
// }

// function syncInput(numId, rangeId) {
//   const numInput = document.getElementById(numId);
//   const rangeInput = document.getElementById(rangeId);
//   numInput.value = rangeInput.value;
//   updateAllSliderFills();
//   if (adWatched) {
//     calculate();
//   }
// }

// function syncSlider(numId, rangeId) {
//   const numInput = document.getElementById(numId);
//   const rangeInput = document.getElementById(rangeId);
//   rangeInput.value = numInput.value;
//   updateAllSliderFills();
//   if (adWatched) {
//     calculate();
//   }
// }


// function calculate() {
//   if (!adWatched) {
//     //showPlaceholders();
//     return;
//   }

//   // let category = document.querySelector('.nav-link.active')?.id;
//   category = document.querySelector('.nav-link.active')?.id;

//   //let ids = [];
//   //let units = [];
//   //let labels = [];
//   let emojis = [];
//   let tooltips = [];

//   calculatedResults = {};


//   if (category === "green-tab") {
//     const trees = +document.getElementById("trees").value || 0;
//     const species = +document.getElementById("species").value || 0;
//     let area = +document.getElementById("area").value || 0;
//     const duration = +document.getElementById("duration").value || 0;
//     const areaUnit = document.querySelector('input[name="btnradio-area"]:checked')?.value || "m2";

//     inputData = [trees, species, area, duration];

//     inputUnits[category][2] = "m²";

//     if (areaUnit === "ac"){
//       area *= 4046.86;
//       inputUnits[category][2] = "ac";

//     } 

//     // calculatedResults = {
//     //   co2: (trees * 21.8).toFixed(1),
//     //   biodiversity: area > 0 ? ((species / area) * 100).toFixed(2) : 0,
//     //   cooling: ((area / 100) * 0.2).toFixed(2),
//     //   air: (trees * 0.12).toFixed(2),
//     //   stormwater: (area * 100).toFixed(0),
//     //   branding: Math.log(trees + species + duration || 1).toFixed(2)
//     // };

//     const co2 = trees * 21.8;
//     const biodiversity = area > 0 ? ((species / area) * 100) : 0;
//     const cooling = (area / 100) * 0.2;
//     const air = trees * 0.12;
//     const stormwater = area * 100;
//     const branding = Math.log(trees + species + duration || 1);


//     const cars = co2 / 1710;
//     const households = co2 / 3000;
//     const credits = co2 / 1000;


//       ids = [
//       "co2",
//       "biodiversity",
//       "cooling",
//       "air",
//       "stormwater",
//       "branding",
//       "cars",
//       "households",
//       "credits"
//     ];

//     units = [
//       "kg/year",
//       "",
//       "°C",
//       "kg/year",
//       "L/year",
//       "",
//       "cars/year",
//       "household years",
//       "credits (1 tCO₂)"
//     ];

//     labels = [
//       "Annual CO₂ Sequestration",
//       "Biodiversity Potential Index",
//       "Localized Cooling Effect",
//       "Air Quality Improvement",
//       "Stormwater Runoff Reduction",
//       "Green Branding Score",
//       "Cars Taken Off the Road",
//       "Household Electricity Offset (Annual)",
//       "Carbon Credits (Approx.)"
//     ];

//     emojis = [
//       "🌳",
//       "🌿",
//       "🌡️",
//       "💨",
//       "💧",
//       "⭐",
//       "🚗",
//       "🏠",
//       "🌲"
//     ];

//     tooltipContent = ["Estimated carbon captured annually by the trees. Removes harmful carbon dioxide from the atmosphere each year, helping slow climate change.", "Relative biodiversity score based on species richness per area. Shows how effectively the green space can support diverse plant and animal life.", "Cooling potential created by green space. Reduces surrounding temperatures naturally, improving comfort and lowering heat stress.", "Amount of PM2.5 removed by trees annually. Filters pollutants like PM2.5 from the air, providing cleaner and healthier air to breathe.", "Rainwater intercepted by green surfaces annually. Absorbs rainfall and reduces flooding risk while improving groundwater replenishment.", "A maturity indicator combining age, species, and trees. Reflects the environmental leadership and maturity of your green initiative.", "Equivalent number of average petrol cars' annual CO₂ emissions avoided.", "Number of average households' annual electricity use offset by saved emissions.", "Approximate number of 1-tonne CO₂ credits represented."];


//     calculatedResults = {
//       co2: co2.toFixed(1),
//       biodiversity: biodiversity.toFixed(2),
//       cooling: cooling.toFixed(2),
//       air: air.toFixed(2),
//       stormwater: stormwater.toFixed(0),
//       branding: branding.toFixed(2),


//       cars: cars.toFixed(2),
//       households: households.toFixed(2),
//       credits: credits.toFixed(2)
//     };
//   }


//   else if (category === "energy-tab") {
//   const electricity = +document.getElementById("electricity").value || 0;
//   const renewable = +document.getElementById("renewable").value || 0;
//   const power = +document.getElementById("powerRating").value || 0;
//   const hours = +document.getElementById("operatingHours").value || 0;

//   inputData = [
//     electricity,
//     renewable,
//     power,
//     hours
//   ];


//   const tariff = 8;
//   const gridEF = 0.82;
//   const baseline = 10000;


//   ids = [
//     "annualEnergy",
//     "energyCost",
//     "renewableShare",
//     "energyIntensity",
//     "energySavings",
//     "ghg",
//     "householdMonths",
//     "petrolAvoided",
//     "energyGJ"
//   ];

//   units = [
//     "kWh/year",
//     "₹/year",
//     "%",
//     "kWh/unit",
//     "%",
//     "kg CO₂/year",
//     "months",
//     "litres",
//     "GJ/year"
//   ];

//   labels = [
//     "Annual Energy",
//     "Energy Cost",
//     "Renewable Share",
//     "Energy Intensity",
//     "Energy Savings",
//     "GHG Emissions",
//     "Household Electricity (Months)",
//     "Petrol Avoided",
//     "Annual GJ Saved"
//   ];

//   emojis = [
//     "⚡️",
//     "💰",
//     "🌞",
//     "📊",
//     "💡",
//     "🌍",
//     "🏠",
//     "⛽",
//     "🔥"
//   ];

//   tooltipContent = ["Total energy consumed annually. Represents the total energy consumed annually, helping track operational efficiency.", "Estimated cost of consumed electricity. Shows the annual financial cost of electricity consumption to highlight savings opportunities.", "Percentage share of renewable energy. Indicates how much of your total energy comes from clean, renewable sources.", "Energy needed per unit of user-defined output. Reveals the amount of energy required per unit of output, showing operational efficiency.", "Reduction in energy use relative to baseline. Shows how much energy you have saved compared to the baseline, demonstrating improvement.", "Emissions caused by electricity usage. Quantifies the climate-impacting emissions generated from electricity use.", "Equivalent months of an average household's electricity supplied by saved energy.", "Volume of petrol whose combustion equals the energy saved.", "Energy savings expressed in gigajoules."];
  

//   const annualEnergy = power * hours * 365;

//   const energyCost = electricity * tariff;
//   const renewableShare = electricity > 0 ? (renewable / electricity) * 100 : 0;
//   const energyIntensity = annualEnergy / 100;
//   const energySavings = ((baseline - electricity) / baseline) * 100;
//   const ghg = electricity * gridEF;


//   const householdMonths = annualEnergy / 90;
//   const petrolAvoided = annualEnergy / 9.7;
//   const energyGJ = annualEnergy / 277.778;


//   calculatedResults = {
//     annualEnergy: annualEnergy.toFixed(2),
//     energyCost: energyCost.toFixed(2),
//     renewableShare: renewableShare.toFixed(2),
//     energyIntensity: energyIntensity.toFixed(2),
//     energySavings: energySavings.toFixed(2),
//     ghg: ghg.toFixed(2),


//     householdMonths: householdMonths.toFixed(2),
//     petrolAvoided: petrolAvoided.toFixed(2),
//     energyGJ: energyGJ.toFixed(2)
//   };
// }


//   else if (category === "water-tab") {
//   const withdrawal = +document.getElementById("waterWithdrawal").value || 0;
//   const discharge = +document.getElementById("waterDischarged").value || 0;
//   const reuse = +document.getElementById("waterReused").value || 0;
//   let siteArea = +document.getElementById("siteArea").value || 0;
//   const siteAreaUnit = document.querySelector('input[name="btnradio-siteArea"]:checked')?.value || "m2";

//   inputData = [
//     withdrawal,
//     discharge,
//     reuse,
//     siteArea
//   ];

//   inputUnits[category][3] = "m²";

//   if (siteAreaUnit === "ac"){
//     siteArea *= 4046.86;
//     inputUnits[category][3] = "ac";
//   } 

//   const netConsumption = withdrawal - discharge - reuse;


//   ids = [
//     "totalUse",
//     "netConsumption",
//     "reusePercent",
//     "stormInfiltration",
//     "waterIntensity",
//     "hydroBalance",
//     "showersSupplied",
//     "householdMonthsWater",
//     "olympicPools"
//   ];

//   units = [
//     "L/year",
//     "L/year",
//     "%",
//     "L/year",
//     "L/m²",
//     "L/year",
//     "showers",
//     "household-months",
//     "pools"
//   ];

//   labels = [
//     "Total Use",
//     "Net Consumption",
//     "Reuse %",
//     "Storm Infiltration",
//     "Water Intensity",
//     "Hydro Balance",
//     "Household Showers Supplied",
//     "Months of Household Water Supply",
//     "Olympic Pools Equivalent"
//   ];

//   emojis = [
//     "💧",
//     "🚰",
//     "🔁",
//     "🌧️",
//     "📊",
//     "⚖️",
//     "🚿",
//     "🏠",
//     "🏊‍♂️"
//   ];

//   tooltipContent = ["Total water withdrawn from all sources. Measures the total water withdrawn from all sources for your operations.", "Water consumed after reuse and discharge. Shows the actual water consumed after subtracting reused and discharged water.", "Percentage of withdrawn water reused. Indicates how effectively your system recycles water, reducing freshwater demand.", "Estimated annual stormwater infiltration. Estimates how much rainwater your site can naturally filter back into the ground.", "Water consumption per output unit. Shows how much water is consumed per unit of output, helping identify efficiency gains.", "Water retained or released by site. Indicates whether your site retains or releases water overall.", "Number of typical household showers that volume of water could supply.", "Months of water supply for one household (basic use) provided.", "Number of standard Olympic pools worth of water saved."];
  


//   const totalUse = withdrawal;
//   const reusePercent = withdrawal > 0 ? (reuse / withdrawal) * 100 : 0;
//   const stormInfiltration = siteArea * 80;
//   const waterIntensity = netConsumption / 100;
//   const hydroBalance = withdrawal - discharge;


//   const litresSaved = reuse;
//   const showersSupplied = litresSaved / 50;
//   const householdMonthsWater = litresSaved / 3000;
//   const olympicPools = litresSaved / 2_500_000;


//   calculatedResults = {
//     totalUse: totalUse.toFixed(2),
//     netConsumption: netConsumption.toFixed(2),
//     reusePercent: reusePercent.toFixed(2),
//     stormInfiltration: stormInfiltration.toFixed(0),
//     waterIntensity: waterIntensity.toFixed(2),
//     hydroBalance: hydroBalance.toFixed(2),


//     showersSupplied: showersSupplied.toFixed(2),
//     householdMonthsWater: householdMonthsWater.toFixed(2),
//     olympicPools: olympicPools.toFixed(4)
//   };
// }


//   else if (category === "waste-tab") {
//   const haz = +document.getElementById("hazardousWaste").value || 0;
//   const nonHaz = +document.getElementById("nonHazardousWaste").value || 0;
//   const recycled = +document.getElementById("wasteRecycled").value || 0;
//   const landfill = +document.getElementById("wasteLandfill").value || 0;

//   inputData = [haz, nonHaz, recycled, landfill];

//   const organicFraction = 0.3;
//   const energyFactor = 0.7;

//   const total = haz + nonHaz;
//   const organicWaste = total * organicFraction;


//   ids = [
//     "totalWaste",
//     "recycleRate",
//     "landfillRate",
//     "energyPotential",
//     "wasteIntensity",
//     "reductionPercent",
//     "truckloadsAvoided",
//     "treeCarbonEquivalent",
//     "energyGenPotential"
//   ];

//   units = [
//     "kg/year",
//     "%",
//     "%",
//     "kWh/year",
//     "kg/m²",
//     "%",
//     "truckloads",
//     "tree-equivalents",
//     "kWh/year"
//   ];

//   labels = [
//     "Total Waste",
//     "Recycle Rate",
//     "Landfill Rate",
//     "Energy Potential",
//     "Waste Intensity",
//     "Reduction %",
//     "Truckloads of Waste Avoided",
//     "Trees Worth of Carbon Avoided",
//     "Energy Generation Potential"
//   ];

//   emojis = [
//     "🗑️",
//     "♻️",
//     "🏭",
//     "⚡",
//     "📊",
//     "📉",
//     "🚛",
//     "🌳",
//     "🔋"
//   ];

//   tooltipContent = ["Combined hazardous and non-hazardous waste. Represents the combined hazardous and non-hazardous waste produced annually.", "Percentage of waste recycled. Shows the percentage of waste diverted from disposal through recycling.", "Percentage of waste landfilled. Indicates how much waste ends up in landfills, supporting zero-waste goals.", "Potential energy from recoverable waste. Shows how much usable energy can be recovered from organic waste.", "Waste generated per output unit. Measures waste generated per unit of output, highlighting efficiency improvements.", "Reduction in waste compared to baseline. Shows how effectively waste has been reduced compared to your baseline levels.", "Number of standard 10-tonne truckloads reduced.", "Approximate trees' worth of carbon avoided by diverting waste.", "Potential electricity from waste-to-energy for organic fraction."]



//   const recycleRate = total > 0 ? (recycled / total) * 100 : 0;
//   const landfillRate = total > 0 ? (landfill / total) * 100 : 0;
//   const energyPotential = total * organicFraction * energyFactor;
//   const wasteIntensity = total / 100;
//   const reductionPercent = ((10000 - total) / 10000) * 100;


//   const truckloadsAvoided = total / 10_000;
//   const treeCarbonEquivalent = total / 1000;
//   const energyGenPotential = organicWaste * 0.7;


//   calculatedResults = {
//     totalWaste: total.toFixed(2),
//     recycleRate: recycleRate.toFixed(2),
//     landfillRate: landfillRate.toFixed(2),
//     energyPotential: energyPotential.toFixed(2),
//     wasteIntensity: wasteIntensity.toFixed(2),
//     reductionPercent: reductionPercent.toFixed(2),


//     truckloadsAvoided: truckloadsAvoided.toFixed(2),
//     treeCarbonEquivalent: treeCarbonEquivalent.toFixed(2),
//     energyGenPotential: energyGenPotential.toFixed(2)
//   };
// }




//     document.querySelectorAll("#report-section .metric-value").forEach((el, index) => {
//       el.id = ids[index];

//     });

//     document.querySelectorAll("#report-section .metric-unit").forEach((el, index) => {
//       el.textContent = units[index];
//     });

//     document.querySelectorAll("#report-section .metric-label").forEach((el, index) => {
//       el.textContent = labels[index];
//     });

//     document.querySelectorAll("#report-section .metric-icon").forEach((el, index) => {
//       el.textContent = emojis[index];
//     });

//     document.querySelectorAll("#report-section .custom-tooltip").forEach((el, index) => {
//       el.textContent = tooltipContent[index];
//     });



    


//   if (isCalculatorPage) {
//     for (const key in calculatedResults) {
//       if (document.getElementById(key))
//         //console.log("Key: " + key + ", Value: " + calculatedResults[key]);
//         formatMetricValues(calculatedResults[key], key);
//     }

//     document.querySelectorAll('.metric-value').forEach(el =>
//       el.classList.add('unlocked')
//     );
//   }
// }






// function showPlaceholders() {
 
//   const category = document.querySelector('.nav-link.active')?.id;

  
//   // const placeholders = {
//   //   "green-tab": ["co2", "biodiversity", "cooling", "air", "stormwater", "branding"],
//   //   "energy-tab": ["annualEnergy", "energyCost", "renewableShare", "energyIntensity", "energySavings", "ghg"],
//   //   "water-tab": ["totalUse", "netConsumption", "reusePercent", "stormInfiltration", "waterIntensity", "hydroBalance"],
//   //   "waste-tab": ["totalWaste", "recycleRate", "landfillRate", "energyPotential", "wasteIntensity", "reductionPercent"]
//   // };
//   const placeholders = {
//     "green-tab": ["co2", "biodiversity", "cooling", "air", "stormwater", "branding"],
//     "energy-tab": ["annualEnergy", "energyCost", "renewableShare", "energyIntensity", "energySavings", "ghg"],
//     "water-tab": ["totalUse", "netConsumption", "reusePercent", "stormInfiltration", "waterIntensity", "hydroBalance"],
//     "waste-tab": ["totalWaste", "recycleRate", "landfillRate", "energyPotential", "wasteIntensity", "reductionPercent"]
//   };

  
//   const ids = placeholders[category] || [];

  
//   ids.forEach(id => {
//     const el = document.getElementById(id);
//     if (el) el.textContent = "••••";
//   });
// }

// if(isIndexPage){
//   updateAllSliderFills();
//   //showPlaceholders();
//   hideActionButtons();
// }

// function formatMetricValues(value, className) {
//   const [intPart, decPart] = Number(value).toFixed(2).split('.');
//   if(decPart === undefined) {
//     document.getElementById(className).innerHTML = value;
//     return;
//   }
//   intPartFormatted = parseInt(intPart.replace(/,/g, '')).toLocaleString();

//   //console.log(value + " : " + className);


//   document.getElementById(className).innerHTML = `${intPartFormatted}.<span class="decimal">${decPart}</span>`;
// }




// function disableForm() {
//   document.querySelectorAll('input[type="number"], input[type="range"], input[type="radio"]').forEach(input => {
//     input.disabled = true;
//     input.style.borderColor = '#e9ebee';
    
//   });

//   document.querySelectorAll('.number-with-unit').forEach(el => {
//     el.style.backgroundColor = '#e9ebee';
//     el.style.border = "1px solid #e9ebee";
//   });
// }

// function enableForm() {
//   document.querySelectorAll('input[type="number"], input[type="range"], input[type="radio"]').forEach(input => {
//     input.disabled = false;
//     input.style.borderColor = '#a7e6bf';
//     updateAllSliderFills();
//   });
//   document.querySelectorAll('input[type="number"], input[type="range"]').forEach(input => {
//     input.value = 0;
//   });
//   document.querySelectorAll('.number-with-unit').forEach(el => {
//     el.style.backgroundColor = '#e9fbf4';
//     el.style.border = "1px solid rgba(167, 230, 191, 1)";
//   });
// }


// function showActionButtons() {
//   const actionContainer = document.getElementById('action-buttons');
//   if (actionContainer) {
//     actionContainer.style.display = 'flex';
//   }
// }

// function hideActionButtons() {
//   const actionContainer = document.getElementById('action-buttons');
//   if (actionContainer) {
//     actionContainer.style.display = 'none';
//   }
// }


// function watchAd() {
  
//   let adButton = document.getElementById('watchAdBtn') || null;
//   const adOverlay = document.getElementById('adOverlay');
//   const adVideo = document.getElementById('adVideo');

//   if (!adOverlay || !adVideo) {
//     console.warn("Ad overlay or video element not found. Aborting watchAd.");
//     if (adButton) {
      
//       adButton.disabled = true;
//       adButton.textContent = 'Playing Ad...';
//       setTimeout(onAdComplete, 800);
//     }
//     return;
//   }

  
//   adOverlay.style.display = 'flex';
//   adVideo.currentTime = 0;
//   const playPromise = adVideo.play();
//   if (playPromise && typeof playPromise.catch === 'function') {
//     playPromise.catch(err => {
//       console.warn("Autoplay prevented. Simulating ad play.", err);
      
//       setTimeout(() => {
//         adOverlay.style.display = 'none';
//         onAdComplete();
//       }, 1000);
//     });
//   }

  
//   document.body.style.overflow = 'hidden';

//   adVideo.onended = () => {
//     adOverlay.style.display = 'none';
//     document.body.style.overflow = 'auto';
//     onAdComplete();
//   };

//   adVideo.onerror = () => {
//     console.warn('Ad failed to load. Simulating completion.');
//     adOverlay.style.display = 'none';
//     document.body.style.overflow = 'auto';
//     setTimeout(onAdComplete, 1000);
//   };

  
//   if (isCalculatorPage() && adButton) {
//     adButton.disabled = true;
//     adButton.textContent = 'Playing Ad...';
//   }
// }
  

// async function onAdComplete() {
//   console.log("Ad complete handler running");
//   adWatched = true;

//   if (isCalculatorPage()) {
//     const reportSection = document.getElementById('report-section');
//     if (reportSection) reportSection.style.display = 'block';
//     try {
      
//       if (reportSection && reportSection.scrollIntoView) {
//         reportSection.scrollIntoView({ behavior: 'smooth' });
//       }
//     } catch (err) {
//       console.warn("scrollIntoView failed:", err);
//     }

    
//     try {
//       calculate();
//     } catch (err) {
//       console.error("calculate() threw:", err);
//     }
//     disableForm();

//     const adButton = document.getElementById('watchAdBtn');
//     const againButton = document.getElementById('generateAgainBtn') || document.getElementById('generateAgain');
//     if (adButton) adButton.style.display = 'none';
//     if (againButton) againButton.style.display = 'inline-block';
//     showActionButtons();
//   }

  
//   try {
//     const pdfBlob = await generatePDFBlob();
//     if (pdfBlob && typeof saveAs === 'function') {
//       saveAs(pdfBlob, "Green_Calculator_Report.pdf");
//     } else {
//       console.log("PDF blob created but saveAs not available / not invoked.");
//     }
//   } catch (err) {
//     console.error("Error generating PDF:", err);
//   }
// }


// function generateAgain() {
//   adWatched = false;
//   calculatedResults = null;

//   document.getElementById('report-section').style.display = 'none';
  
//   //showPlaceholders();
//   enableForm();
//   hideActionButtons();
//   updateAllSliderFills();

//   document.querySelectorAll('.metric-value').forEach(el => {
//     el.classList.remove('unlocked');
//   });
  
  
//   const adButton = document.getElementById('watchAdBtn');
//   const generateAgainBtn = document.getElementById('generateAgainBtn');
//   if (adButton) {
//     adButton.style.display = 'inline-block';
//     adButton.innerHTML = "<i class='bi bi-play-circle'></i> Generate Metrics";
//     adButton.disabled = false;
//   }

//   if(generateAgainBtn) {
//     generateAgainBtn.style.display = 'none';
//   }
  
  
//   window.scrollTo({ top: 0, behavior: 'smooth' });
// }











// const reportIds = [];

// async function generatePDFBlob() {
//       const response = await fetch("https://arkraj7.github.io/csid/Leaf-and-Ledger/report.html");
//       const html = await response.text();
//       const parser = new DOMParser();
//       const doc = parser.parseFromString(html, "text/html");
      

//       doc.querySelectorAll(".overview-label").forEach((label, index) => {
//         //console.log(label);
//         label.textContent = inputHeaders[category][index];
//       });

//       doc.querySelectorAll(".overview-value").forEach((value, index) => {
//         //value.textContent = inputData[index];
//         value.innerHTML = `${inputData[index]} <span>${inputUnits[category][index]}</span>`;
//       });

//       // doc.querySelectorAll(".overview-value span").forEach((unit, index) => {
//       //   console.log(unit);
//       //   unit.innerHTML = inputUnits[category][index];
//       // });

      

//       doc.querySelectorAll(".impact-section .impact-card .impact-label").forEach((label, index) => {
//         label.textContent = labels[index];
//       });

//       //console.log(reportIds);

//       console.log(doc.querySelectorAll(".overview-value"));

//       doc.querySelectorAll(".impact-section .impact-card .impact-unit").forEach((unit, index) => {
//         unit.textContent = units[index];
//       });

//       doc.querySelectorAll(".impact-section .impact-card .impact-value").forEach((value, index) => {
//         //value.textContent = calculatedResults[index];
//         //value.id = reportIds[index] + "-value";
//         value.id = ids[index] + "-value";
//       });

//     //   for (const key in calculatedResults) {
//     //     //console.log(key);
//     //   if (doc.getElementById(key + "-value")){
//     //     //console.log(doc.getElementById(key + "-value"));
//     //     //console.log(calculatedResults[key]);
//     //     doc.getElementById(key + "-value").textContent = calculatedResults[key];
//     //   }
//     //     //console.log("Key: " + key + ", Value: " + calculatedResults[key]);
//     //     //formatMetricValues(calculatedResults[key], key);
//     //     //console.log(document.getElementById(key + "-value"));

        
//     // }

//     for(const key in calculatedResults){
//       console.log(key + "-value");
//       doc.getElementById(key + "-value").textContent = calculatedResults[key];
//     }



      



      
//       const now = new Date();
//       const formattedDate = now.toLocaleDateString('en-GB').replace(/\//g, '.') + 
//                            ', ' + 
//                            now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
//       doc.querySelector("#report-date").textContent = formattedDate;


//       const reportDiv = doc.getElementById("report");
//       reportDiv.style.width = "210mm";
//       reportDiv.style.minHeight = "297mm";
//       reportDiv.style.background = "#fff";
//       reportDiv.style.boxSizing = "border-box";


//       document.body.appendChild(reportDiv);

//       const canvas = await html2canvas(reportDiv, { 
//         scale: 2, 
//         useCORS: true, 
//         backgroundColor: "#ffffff",
//         logging: false
//       });
//       const imgData = canvas.toDataURL("image/jpeg", 0.95);

//       const pdf = new jspdf.jsPDF("p", "mm", "a4");
//       const pageWidth = pdf.internal.pageSize.getWidth();
//       const pageHeight = pdf.internal.pageSize.getHeight();

//       const imgWidth = pageWidth;
//       const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
//       let finalHeight, finalWidth, xOffset, yOffset;
      
//       if (imgHeight > pageHeight) {
//         finalHeight = pageHeight;
//         finalWidth = (pageHeight * canvas.width) / canvas.height;
//       } else {
//         finalHeight = imgHeight;
//         finalWidth = imgWidth;
//       }
      
//       xOffset = (pageWidth - finalWidth) / 2;
//       yOffset = (pageHeight - finalHeight) / 2;

//       pdf.addImage(imgData, "JPEG", xOffset, yOffset, finalWidth, finalHeight);
//       const blob = pdf.output("blob");


//       reportDiv.remove();
      
//       return blob;
//     }













const path = window.location.pathname;
const isIndexPage = path.endsWith("index.html") || path.endsWith("/") || path === "" || path.includes("index");
const isReportPage = path.includes("report");
const isCalculatorPage = () => window.location.pathname.includes("calculator.html") || window.location.pathname.includes("green-calculator-app.html");

let chart;
let areaUnit = "m2";
let adWatched = false;
let selectedUnit = "m2";
let calculatedResults = null;
let category = "green-tab";
let inputData = ["0", "0", "0", "0"];

let previewHeaderText = "";
let previewContentText = "";

const inputHeaders = {
  "green-tab": ["Number of Trees", "Number of Species", "Area", "Project Duration"],
  "energy-tab": ["Electricity Consumption", "Renewable Electricity Used", "Power Rating of Equipment", "Operating Hours per Day"],
  "water-tab": ["Water Withdrawal", "Water Discharged", "Water Reused", "Site Area"],
  "waste-tab": ["Hazardous Waste", "Non-Hazardous Waste", "Waste Recycled", "Waste Sent to Landfill"]
};

// const icons = {
//   "green-tab": ["icons-removebg-preview.png", "icons_copy-removebg-preview.png", "icons_copy_3-removebg-preview.png", "icons_copy_4-removebg-preview.png", "icons_copy_2-removebg-preview.png", "icons_copy_5-removebg-preview.png", "icons_copy_7-removebg-preview.png", "icons_copy_6-removebg-preview.png", "icons_copy_8-removebg-preview.png"],
//   "energy-tab": ["Energy-removebg-preview.png", "Energy_copy-removebg-preview.png", "Energy_copy_2-removebg-preview.png", "Energy_copy_3-removebg-preview.png", "Energy_copy_4-removebg-preview.png", "Energy_copy_5-removebg-preview.png", "Energy_copy_6-removebg-preview.png", "Energy_copy_7-removebg-preview.png", "Energy_copy_8-removebg-preview.png"],
//   "water-tab": ["Water-removebg-preview.png", "Water_copy-removebg-preview.png", "Water_copy_2-removebg-preview.png", "Water_copy_3-removebg-preview.png", "Water_copy_4-removebg-preview.png", "Water_copy_5-removebg-preview.png", "Water_copy_6-removebg-preview.png", "Water_copy_7-removebg-preview.png", "Water_copy_8-removebg-preview.png"],
//   "waste-tab": ["Waste-removebg-preview.png", "Waste_copy-removebg-preview.png", "Waste_copy_2-removebg-preview.png", "Waste_copy_3-removebg-preview.png", "Waste_copy_4-removebg-preview.png", "Waste_copy_5-removebg-preview.png", "Waste_copy_6-removebg-preview.png", "Waste_copy_7-removebg-preview.png", "Waste_copy_8-removebg-preview.png"]
// }

let iconsToUse = [];

const inputUnits = {
  "green-tab": ["", "", "m²", "years"],
  "energy-tab": ["kWh/year", "kWh/year", "kW", "hours/day"],
  "water-tab": ["Litres/year", "Litres/year", "Litres/year", "m²"],
  "waste-tab": ["kg/year", "kg/year", "kg", "m²"]
};

function formatNumberPretty(value) {
    const num = Number(value);
    if (isNaN(num)) return value;

    const parts = num.toString().split(".");
    const integer = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    const decimal = parts[1] ? "." + parts[1] : "";

    return integer + decimal;
}

let tooltipContent = [];
let labels = [];
let units = [];
let ids = [];

const infoIcons = document.querySelectorAll(".branding-info");
const tooltips = document.querySelectorAll(".branding-tooltip");

infoIcons.forEach((infoIcon, index) => {
  const tooltip = tooltips[index];
  infoIcon.addEventListener('click', (e) => {
    tooltips.forEach(t => {
      if (t !== tooltip) t.style.display = 'none';
    });
    tooltip.style.display = tooltip.style.display === 'block' ? 'none' : 'block';
    e.stopPropagation();
  });
});

document.addEventListener('click', (e) => {
  infoIcons.forEach((infoIcon, index) => {
    const tooltip = tooltips[index];
    if (!infoIcon.contains(e.target) && !tooltip.contains(e.target)) {
      tooltip.style.display = 'none';
    }
  });
});

  function initAreaDivValues() {
    document.querySelectorAll(".area-div").forEach(areaDiv => {
      const numInput = areaDiv.querySelector(".number-with-unit input[type='number']");
      const unitSpan = areaDiv.querySelector(".number-with-unit span");
      if (!numInput) return;
      const checkedUnit = areaDiv.querySelector("input[type='radio']:checked")?.value || "m2";
      const displayVal = parseFloat(numInput.value) || 0;
      numInput.dataset.m2 = m2FromDisplay(displayVal, checkedUnit);
      if (unitSpan) unitSpan.textContent = checkedUnit === 'ac' ? 'ac' : 'm²';
      const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");
      if (rangeInput) {
        rangeInput.max = checkedUnit === 'ac' ? 2.5 : 10000;
        rangeInput.value = displayVal;
      }
    });
  }

//document.addEventListener("DOMContentLoaded", () => {
  const AC_TO_M2 = 4046.86;

  // function displayFromM2(m2, unit) {
  //   return unit === "ac" ? m2 / AC_TO_M2 : m2;
  // }

  // function m2FromDisplay(displayValue, unit) {
  //   return unit === "ac" ? displayValue * AC_TO_M2 : displayValue;
  // }

  // function initAreaDivValues() {
  //   document.querySelectorAll(".area-div").forEach(areaDiv => {
  //     const numInput = areaDiv.querySelector(".number-with-unit input[type='number']");
  //     const unitSpan = areaDiv.querySelector(".number-with-unit span");
  //     if (!numInput) return;
  //     const checkedUnit = areaDiv.querySelector("input[type='radio']:checked")?.value || "m2";
  //     const displayVal = parseFloat(numInput.value) || 0;
  //     numInput.dataset.m2 = m2FromDisplay(displayVal, checkedUnit);
  //     if (unitSpan) unitSpan.textContent = checkedUnit === 'ac' ? 'ac' : 'm²';
  //     const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");
  //     if (rangeInput) {
  //       rangeInput.max = checkedUnit === 'ac' ? 2.5 : 10000;
  //       rangeInput.value = displayVal;
  //     }
  //   });
  // }

  function updateAreaDiv(areaDiv, chosenUnit) {
    const numInput = areaDiv.querySelector(".number-with-unit input[type='number']");
    const unitSpan = areaDiv.querySelector(".number-with-unit span");
    const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");
    if (!numInput || !unitSpan) return;
    const m2 = parseFloat(numInput.dataset.m2) || 0;
    const newDisplay = displayFromM2(m2, chosenUnit);
    numInput.value = Number(newDisplay.toFixed(chosenUnit === 'ac' ? 4 : 2));
    unitSpan.textContent = chosenUnit === 'ac' ? 'ac' : 'm²';
    if (rangeInput) {
      rangeInput.max = chosenUnit === 'ac' ? 2.5 : 10000;
      rangeInput.value = numInput.value;
    }
    updateAllSliderFills();
    if (adWatched) calculate();
  }

  document.addEventListener('input', e => {
    if (!e.target.matches(".area-div .number-with-unit input[type='number']")) return;
    const numInput = e.target;
    const areaDiv = numInput.closest(".area-div");
    if (!areaDiv) return;
    const curUnit = areaDiv.querySelector("input[type='radio']:checked")?.value || "m2";
    const displayVal = parseFloat(numInput.value) || 0;
    numInput.dataset.m2 = m2FromDisplay(displayVal, curUnit);
    const rangeInput = areaDiv.closest(".form-group")?.querySelector("input[type='range']");
    if (rangeInput) rangeInput.value = displayVal;
    updateAllSliderFills();
    if (adWatched) calculate();
  });

  document.addEventListener('change', e => {
    if (!e.target.matches(".area-div input[type='radio']")) return;
    const radio = e.target;
    const areaDiv = radio.closest(".area-div");
    if (!areaDiv) return;
    const chosenUnit = radio.value;
    updateAreaDiv(areaDiv, chosenUnit);
  });

  initAreaDivValues();

  const generateBtn = document.getElementById("generateAgain") || document.getElementById("generateAgainBtn");
  if (generateBtn) {
    generateBtn.addEventListener("click", () => {
      requestAnimationFrame(initAreaDivValues);
    });
  }
//});

  function displayFromM2(m2, unit) {
    return unit === "ac" ? m2 / AC_TO_M2 : m2;
  }

  function m2FromDisplay(displayValue, unit) {
    return unit === "ac" ? displayValue * AC_TO_M2 : displayValue;
  }

function updateAllSliderFills() {
  document.querySelectorAll('input[type="range"]').forEach(slider => {
    const min = parseFloat(slider.min) || 0;
    const max = parseFloat(slider.max) || 100;
    const val = parseFloat(slider.value) || 0;
    const percent = ((val - min) / (max - min)) * 100;
    slider.style.background = `linear-gradient(to right, #7acb8a 0%, #7acb8a ${percent}%, #f0f0f0 ${percent}%, #f0f0f0 100%)`;
  });
}

function validateNonNegative(input) {
  if (!input) return;
  if (input.value.startsWith("-")) {
    input.value = input.value.replace("-", "");
  }
}

function syncInput(numId, rangeId) {
  const numInput = document.getElementById(numId);
  const rangeInput = document.getElementById(rangeId);
  if (!numInput || !rangeInput) return;
  numInput.value = rangeInput.value;
  updateAllSliderFills();
  if (adWatched) calculate();
}

function syncSlider(numId, rangeId) {
  const numInput = document.getElementById(numId);
  const rangeInput = document.getElementById(rangeId);
  if (!numInput || !rangeInput) return;
  rangeInput.value = numInput.value;
  updateAllSliderFills();
  if (adWatched) calculate();
}

function calculate() {
  if (!adWatched) return;
  category = document.querySelector('.nav-link.active')?.id || category;
  let emojisLocal = [];
  tooltipContent = [];
  calculatedResults = {};
  //iconsToUse = icons[category] || [];
  if (category === "green-tab") {
    const trees = +document.getElementById("trees")?.value || 0;
    const species = +document.getElementById("species")?.value || 0;
    let area = +document.getElementById("area")?.value || 0;
    const duration = +document.getElementById("duration")?.value || 0;
    const areaUnitSelected = document.querySelector('input[name="btnradio-area"]:checked')?.value || "m2";
    inputData = [trees, species, area, duration];
    inputUnits[category][2] = "m²";
    if (areaUnitSelected === "ac") {
      area *= 4046.86;
      inputUnits[category][2] = "ac";
    }
    const co2 = trees * 21.8;
    const biodiversity = area > 0 ? ((species / area) * 100) : 0;
    const cooling = (area / 100) * 0.2;
    const air = trees * 0.12;
    const stormwater = area * 100;
    const branding = Math.log(Math.max(1, trees + species + duration));
    const cars = co2 / 1710;
    const households = co2 / 3000;
    const credits = co2 / 1000;
    ids = ["co2","biodiversity","cooling","air","stormwater","branding","cars","households","credits"];
    units = ["kg/year","","°C","kg/year","L/year","","cars/year","household years","credits (1 tCO₂)"];
    labels = ["Annual CO₂ Sequestration","Biodiversity Potential Index","Localized Cooling Effect","Air Quality Improvement","Stormwater Runoff Reduction","Green Branding Score","Cars Taken Off the Road","Household Electricity Offset (Annual)","Carbon Credits (Approx.)"];
    emojisLocal = ["🌳","🌿","🌡️","💨","💧","⭐","🚗","🏠","🌲"];
    tooltipContent = ["Estimated carbon captured annually by the trees. Removes harmful carbon dioxide from the atmosphere each year, helping slow climate change.", "Relative biodiversity score based on species richness per area. Shows how effectively the green space can support diverse plant and animal life.", "Cooling potential created by green space. Reduces surrounding temperatures naturally, improving comfort and lowering heat stress.", "Amount of PM2.5 removed by trees annually. Filters pollutants like PM2.5 from the air, providing cleaner and healthier air to breathe.", "Rainwater intercepted by green surfaces annually. Absorbs rainfall and reduces flooding risk while improving groundwater replenishment.", "A maturity indicator combining age, species, and trees. Reflects the environmental leadership and maturity of your green initiative.", "Equivalent number of average petrol cars' annual CO₂ emissions avoided.", "Number of average households' annual electricity use offset by saved emissions.", "Approximate number of 1-tonne CO₂ credits represented."];
    iconsToUse = ["icons-removebg-preview.png", "icons_copy-removebg-preview.png", "icons_copy_3-removebg-preview.png", "icons_copy_4-removebg-preview.png", "icons_copy_2-removebg-preview.png", "icons_copy_5-removebg-preview.png", "icons_copy_7-removebg-preview.png", "icons_copy_6-removebg-preview.png", "icons_copy_8-removebg-preview.png"];
    previewHeaderText = "Green Space & Biodiversity";
    previewContentText = "This category reflects the quantity and diversity of natural areas, which are vital for supporting ecosystems, species, and urban well-being. Measuring it helps assess how well a site preserves nature and promotes resilience against urban and climate pressures.";
;    calculatedResults = {
      co2: co2.toFixed(1),
      biodiversity: biodiversity.toFixed(2),
      cooling: cooling.toFixed(2),
      air: air.toFixed(2),
      stormwater: stormwater.toFixed(0),
      branding: branding.toFixed(2),
      cars: cars.toFixed(2),
      households: households.toFixed(2),
      credits: credits.toFixed(2)
    };
  } else if (category === "energy-tab") {
    const electricity = +document.getElementById("electricity")?.value || 0;
    const renewable = +document.getElementById("renewable")?.value || 0;
    const power = +document.getElementById("powerRating")?.value || 0;
    const hours = +document.getElementById("operatingHours")?.value || 0;
    inputData = [electricity, renewable, power, hours];
    const tariff = 8;
    const gridEF = 0.82;
    const baseline = 10000;
    const annualEnergy = power * hours * 365;
    const energyCost = electricity * tariff;
    const renewableShare = electricity > 0 ? (renewable / electricity) * 100 : 0;
    const energyIntensity = annualEnergy / 100;
    const energySavings = ((baseline - electricity) / baseline) * 100;
    const ghg = electricity * gridEF;
    const householdMonths = annualEnergy / 90;
    const petrolAvoided = annualEnergy / 9.7;
    const energyGJ = annualEnergy / 277.778;
    ids = ["annualEnergy","energyCost","renewableShare","energyIntensity","energySavings","ghg","householdMonths","petrolAvoided","energyGJ"];
    units = ["kWh/year","₹/year","%","kWh/unit","%","kg CO₂/year","months","litres","GJ/year"];
    labels = ["Annual Energy","Energy Cost","Renewable Share","Energy Intensity","Energy Savings","GHG Emissions","Household Electricity (Months)","Petrol Avoided","Annual GJ Saved"];
    emojisLocal = ["⚡️","💰","🌞","📊","💡","🌍","🏠","⛽","🔥"];
    tooltipContent = ["Total energy consumed annually. Represents the total energy consumed annually, helping track operational efficiency.", "Estimated cost of consumed electricity. Shows the annual financial cost of electricity consumption to highlight savings opportunities.", "Percentage share of renewable energy. Indicates how much of your total energy comes from clean, renewable sources.", "Energy needed per unit of user-defined output. Reveals the amount of energy required per unit of output, showing operational efficiency.", "Reduction in energy use relative to baseline. Shows how much energy you have saved compared to the baseline, demonstrating improvement.", "Emissions caused by electricity usage. Quantifies the climate-impacting emissions generated from electricity use.", "Equivalent months of an average household's electricity supplied by saved energy.", "Volume of petrol whose combustion equals the energy saved.", "Energy savings expressed in gigajoules."];
    iconsToUse = ["Energy-removebg-preview.png", "Energy_copy-removebg-preview.png", "Energy_copy_2-removebg-preview.png", "Energy_copy_3-removebg-preview.png", "Energy_copy_4-removebg-preview.png", "Energy_copy_5-removebg-preview.png", "Energy_copy_6-removebg-preview.png", "Energy_copy_7-removebg-preview.png", "Energy_copy_8-removebg-preview.png"];
    previewHeaderText = "Energy & Built Environment";
    previewContentText = "This category captures how sustainably energy is consumed and managed in buildings and infrastructure. Understanding this allows users to quantify their energy footprint and identify opportunities to reduce emissions and improve efficiency.";
    calculatedResults = {
      annualEnergy: annualEnergy.toFixed(2),
      energyCost: energyCost.toFixed(2),
      renewableShare: renewableShare.toFixed(2),
      energyIntensity: energyIntensity.toFixed(2),
      energySavings: energySavings.toFixed(2),
      ghg: ghg.toFixed(2),
      householdMonths: householdMonths.toFixed(2),
      petrolAvoided: petrolAvoided.toFixed(2),
      energyGJ: energyGJ.toFixed(2)
    };
  } else if (category === "water-tab") {
    const withdrawal = +document.getElementById("waterWithdrawal")?.value || 0;
    const discharge = +document.getElementById("waterDischarged")?.value || 0;
    const reuse = +document.getElementById("waterReused")?.value || 0;
    let siteArea = +document.getElementById("siteArea")?.value || 0;
    const siteAreaUnit = document.querySelector('input[name="btnradio-siteArea"]:checked')?.value || "m2";
    inputData = [withdrawal, discharge, reuse, siteArea];
    inputUnits[category][3] = "m²";
    if (siteAreaUnit === "ac") {
      siteArea *= 4046.86;
      inputUnits[category][3] = "ac";
    }
    const netConsumption = withdrawal - discharge - reuse;
    const totalUse = withdrawal;
    const reusePercent = withdrawal > 0 ? (reuse / withdrawal) * 100 : 0;
    const stormInfiltration = siteArea * 80;
    const waterIntensity = netConsumption / 100;
    const hydroBalance = withdrawal - discharge;
    const litresSaved = reuse;
    const showersSupplied = litresSaved / 50;
    const householdMonthsWater = litresSaved / 3000;
    const olympicPools = litresSaved / 2500000;
    ids = ["totalUse","netConsumption","reusePercent","stormInfiltration","waterIntensity","hydroBalance","showersSupplied","householdMonthsWater","olympicPools"];
    units = ["L/year","L/year","%","L/year","L/m²","L/year","showers","household-months","pools"];
    labels = ["Total Use","Net Consumption","Reuse %","Storm Infiltration","Water Intensity","Hydro Balance","Household Showers Supplied","Months of Household Water Supply","Olympic Pools Equivalent"];
    emojisLocal = ["💧","🚰","🔁","🌧️","📊","⚖️","🚿","🏠","🏊‍♂️"];
    tooltipContent = ["Total water withdrawn from all sources. Measures the total water withdrawn from all sources for your operations.", "Water consumed after reuse and discharge. Shows the actual water consumed after subtracting reused and discharged water.", "Percentage of withdrawn water reused. Indicates how effectively your system recycles water, reducing freshwater demand.", "Estimated annual stormwater infiltration. Estimates how much rainwater your site can naturally filter back into the ground.", "Water consumption per output unit. Shows how much water is consumed per unit of output, helping identify efficiency gains.", "Water retained or released by site. Indicates whether your site retains or releases water overall.", "Number of typical household showers that volume of water could supply.", "Months of water supply for one household (basic use) provided.", "Number of standard Olympic pools worth of water saved."];
    iconsToUse = ["Water-removebg-preview.png", "Water_copy-removebg-preview.png", "Water_copy_2-removebg-preview.png", "Water_copy_3-removebg-preview.png", "Water_copy_4-removebg-preview.png", "Water_copy_5-removebg-preview.png", "Water_copy_6-removebg-preview.png", "Water_copy_7-removebg-preview.png", "Water_copy_8-removebg-preview.png"];
    previewHeaderText = "Water Use & Management";
    previewContentText = "It represents the amount and quality of water utilized and conserved within a site. Tracking water use supports resource planning and sustainability, helping users safeguard against scarcity and pollution risk.";
    
    calculatedResults = {
      totalUse: totalUse.toFixed(2),
      netConsumption: netConsumption.toFixed(2),
      reusePercent: reusePercent.toFixed(2),
      stormInfiltration: stormInfiltration.toFixed(0),
      waterIntensity: waterIntensity.toFixed(2),
      hydroBalance: hydroBalance.toFixed(2),
      showersSupplied: showersSupplied.toFixed(2),
      householdMonthsWater: householdMonthsWater.toFixed(2),
      olympicPools: olympicPools.toFixed(4)
    };
  } else if (category === "waste-tab") {
    const haz = +document.getElementById("hazardousWaste")?.value || 0;
    const nonHaz = +document.getElementById("nonHazardousWaste")?.value || 0;
    const recycled = +document.getElementById("wasteRecycled")?.value || 0;
    const landfill = +document.getElementById("wasteLandfill")?.value || 0;
    inputData = [haz, nonHaz, recycled, landfill];
    const organicFraction = 0.3;
    const energyFactor = 0.7;
    const total = haz + nonHaz;
    const organicWaste = total * organicFraction;
    const recycleRate = total > 0 ? (recycled / total) * 100 : 0;
    const landfillRate = total > 0 ? (landfill / total) * 100 : 0;
    const energyPotential = total * organicFraction * energyFactor;
    const wasteIntensity = total / 100;
    const reductionPercent = ((10000 - total) / 10000) * 100;
    const truckloadsAvoided = total / 10000;
    const treeCarbonEquivalent = total / 1000;
    const energyGenPotential = organicWaste * 0.7;

    ids = ["totalWaste","recycleRate","landfillRate","energyPotential","wasteIntensity","reductionPercent","truckloadsAvoided","treeCarbonEquivalent","energyGenPotential"];
    units = ["kg/year","%","%","kWh/year","kg/m²","%","truckloads","tree-equivalents","kWh/year"];
    labels = ["Total Waste","Recycle Rate","Landfill Rate","Energy Potential","Waste Intensity","Reduction %","Truckloads of Waste Avoided","Trees Worth of Carbon Avoided","Energy Generation Potential"];
    emojisLocal = ["🗑️","♻️","🏭","⚡","📊","📉","🚛","🌳","🔋"];
    tooltipContent = ["Combined hazardous and non-hazardous waste. Represents the combined hazardous and non-hazardous waste produced annually.", "Percentage of waste recycled. Shows the percentage of waste diverted from disposal through recycling.", "Percentage of waste landfilled. Indicates how much waste ends up in landfills, supporting zero-waste goals.", "Potential energy from recoverable waste. Shows how much usable energy can be recovered from organic waste.", "Waste generated per output unit. Measures waste generated per unit of output, highlighting efficiency improvements.", "Reduction in waste compared to baseline. Shows how effectively waste has been reduced compared to your baseline levels.", "Number of standard 10-tonne truckloads reduced.", "Approximate trees' worth of carbon avoided by diverting waste.", "Potential electricity from waste-to-energy for organic fraction."];
    iconsToUse = ["Waste-removebg-preview.png", "Waste_copy-removebg-preview.png", "Waste_copy_2-removebg-preview.png", "Waste_copy_3-removebg-preview.png", "Waste_copy_4-removebg-preview.png", "Waste_copy_5-removebg-preview.png", "Waste_copy_6-removebg-preview.png", "Waste_copy_7-removebg-preview.png", "Waste_copy_8-removebg-preview.png"];
    previewHeaderText = "Waste & Circularity";
    previewContentText = "This category covers the generation, handling, and recycling of waste, emphasizing materials kept in productive use. Measuring waste and circularity highlights environmental responsibility and progress toward minimizing landfill through smart resource cycles.";
    
    calculatedResults = {
      totalWaste: total.toFixed(2),
      recycleRate: recycleRate.toFixed(2),
      landfillRate: landfillRate.toFixed(2),
      energyPotential: energyPotential.toFixed(2),
      wasteIntensity: wasteIntensity.toFixed(2),
      reductionPercent: reductionPercent.toFixed(2),
      truckloadsAvoided: truckloadsAvoided.toFixed(2),
      treeCarbonEquivalent: treeCarbonEquivalent.toFixed(2),
      energyGenPotential: energyGenPotential.toFixed(2)
    };
  } else {
    ids = [];
    units = [];
    labels = [];
    emojisLocal = [];
    tooltipContent = [];
    calculatedResults = {};
  }

  document.querySelectorAll("#report-section .metric-value").forEach((el, index) => {
    if (ids[index]) el.id = ids[index];
  });

  document.querySelectorAll("#report-section .metric-unit").forEach((el, index) => {
    if (units[index] !== undefined) el.textContent = units[index];
  });

  document.querySelectorAll("#report-section .metric-label").forEach((el, index) => {
    if (labels[index] !== undefined) el.textContent = labels[index];
    
  });

  document.querySelectorAll("#report-section .metric-icon").forEach((el, index) => {
    //if (emojisLocal[index] !== undefined) el.textContent = emojisLocal[index];
    if(iconsToUse[index]){
      //el.innerHTML = `<img src="./images/${iconsToUse[index]}" alt="${labels[index]}" class="metric-icon-img" style="height: 48px;">`;
      el.innerHTML = `<img src="https://arkraj7.github.io/csid/Leaf-and-Ledger/images/${iconsToUse[index]}" alt="${labels[index]}" class="metric-icon-img" style="height: 48px;">`;
    }
    //el.innerHTML = iconsToUse[index] ? `<img src="https://arkraj7.github.io/csid/Leaf-and-Ledger/images/${iconsToUse[index]}" alt="${labels[index]}"> ${labels[index]}` : labels[index];
    //el.innerHTML = iconsToUse[index] ? `<img src="./images/${iconsToUse[index]}" alt="${labels[index]}"> ${labels[index]}` : labels[index];
    // class="metric-icon-img"
  });

  document.querySelectorAll("#report-section .custom-tooltip").forEach((el, index) => {
    if (tooltipContent[index] !== undefined) el.textContent = tooltipContent[index];
  });

  

  if (isCalculatorPage()) {
    for (const key in calculatedResults) {
      if (Object.prototype.hasOwnProperty.call(calculatedResults, key)) {
        if (document.getElementById(key)) {
          formatMetricValues(calculatedResults[key], key);
        }
      }
    }
    document.querySelectorAll('.metric-value').forEach(el => el.classList.add('unlocked'));
  }
}

function showPlaceholders() {
  const categoryLocal = document.querySelector('.nav-link.active')?.id || category;
  const placeholders = {
    "green-tab": ["co2","biodiversity","cooling","air","stormwater","branding"],
    "energy-tab": ["annualEnergy","energyCost","renewableShare","energyIntensity","energySavings","ghg"],
    "water-tab": ["totalUse","netConsumption","reusePercent","stormInfiltration","waterIntensity","hydroBalance"],
    "waste-tab": ["totalWaste","recycleRate","landfillRate","energyPotential","wasteIntensity","reductionPercent"]
  };
  const idsLocal = placeholders[categoryLocal] || [];
  idsLocal.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = "••••";
  });
}

if (isIndexPage) {
  updateAllSliderFills();
  hideActionButtons();
}

function formatMetricValues(value, className) {
  const num = Number(value);
  if (Number.isNaN(num)) {
    const el = document.getElementById(className);
    if (el) el.textContent = value;
    return;
  }
  const parts = num.toFixed(2).split('.');
  const intPartFormatted = parseInt(parts[0].replace(/,/g, ''), 10).toLocaleString();
  const decPart = parts[1] || '00';
  const el = document.getElementById(className);
  if (el) el.innerHTML = `${intPartFormatted}.<span class="decimal">${decPart}</span>`;
}

function disableForm() {
  document.querySelectorAll('input[type="number"], input[type="range"], input[type="radio"]').forEach(input => {
    input.disabled = true;
    input.style.borderColor = '#e9ebee';
  });
  document.querySelectorAll('.number-with-unit').forEach(el => {
    el.style.backgroundColor = '#e9ebee';
    el.style.border = "1px solid #e9ebee";
  });
  updateAllSliderFills();
}

function enableForm() {
  document.querySelectorAll('input[type="number"], input[type="range"], input[type="radio"]').forEach(input => {
    input.disabled = false;
    input.style.borderColor = '#a7e6bf';
  });
  document.querySelectorAll('input[type="number"], input[type="range"]').forEach(input => {
    input.value = 0;
  });
  document.querySelectorAll('.number-with-unit').forEach(el => {
    el.style.backgroundColor = '#e9fbf4';
    el.style.border = "1px solid rgba(167, 230, 191, 1)";
  });
  updateAllSliderFills();
}

function showActionButtons() {
  const actionContainer = document.getElementById('action-buttons');
  if (actionContainer) actionContainer.style.display = 'flex';
}

function hideActionButtons() {
  const actionContainer = document.getElementById('action-buttons');
  if (actionContainer) actionContainer.style.display = 'none';
}

let thankYouCountdown = null;

function showThankYouModal() {
  const modal = document.getElementById('thank-you-modal');
  const countdownNumber = document.getElementById('countdown-number');
  if (!modal) return;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  let seconds = 10;
  countdownNumber.textContent = seconds;

  thankYouCountdown = setInterval(() => {
    seconds--;
    countdownNumber.textContent = seconds;
    if (seconds <= 0) {
      clearInterval(thankYouCountdown);
      thankYouCountdown = null;
      hideThankYouModal();
      onAdComplete();
    }
  }, 1000);
}

function hideThankYouModal() {
  const modal = document.getElementById('thank-you-modal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

function startCalculations() {
  const calcButton = document.getElementById('watchAdBtn');
  if (calcButton) {
    calcButton.disabled = true;
    calcButton.textContent = 'Calculating...';
  }
  showThankYouModal();
}

function onThankYouRedirect() {
  if (thankYouCountdown) {
    clearInterval(thankYouCountdown);
    thankYouCountdown = null;
  }
  hideThankYouModal();
  onAdComplete();
}

// Setup manual redirect button
document.addEventListener('DOMContentLoaded', () => {
  const manualBtn = document.getElementById('manual-redirect-btn');
  if (manualBtn) {
    manualBtn.addEventListener('click', onThankYouRedirect);
  }
});

async function onAdComplete() {
  adWatched = true;
  if (isCalculatorPage()) {
    const reportSection = document.getElementById('report-section');
    if (reportSection) reportSection.style.display = 'block';
    try {
      if (reportSection && reportSection.scrollIntoView) reportSection.scrollIntoView({ behavior: 'smooth' });
    } catch (e) {}
    try { calculate(); } catch (e) {}
    disableForm();
    const adButton = document.getElementById('watchAdBtn');
    const againButton = document.getElementById('generateAgainBtn') || document.getElementById('generateAgain');
    if (adButton) adButton.style.display = 'none';
    if (againButton) againButton.style.display = 'inline-block';
    showActionButtons();
  }
  try {
    const pdfBlob = await generatePDFBlob();
    if (pdfBlob && typeof saveAs === 'function') saveAs(pdfBlob, "Green_Calculator_Report.pdf");
  } catch (err) {}
}

function generateAgain() {
  adWatched = false;
  calculatedResults = null;
  const reportSection = document.getElementById('report-section');
  if (reportSection) reportSection.style.display = 'none';
  enableForm();
  hideActionButtons();
  updateAllSliderFills();
  document.querySelectorAll('.metric-value').forEach(el => el.classList.remove('unlocked'));
  const adButton = document.getElementById('watchAdBtn');
  const generateAgainBtn = document.getElementById('generateAgainBtn');
  if (adButton) {
    adButton.style.display = 'inline-block';
    adButton.innerHTML = "<i class='bi bi-play-circle'></i> Generate Metrics";
    adButton.disabled = false;
  }
  if (generateAgainBtn) generateAgainBtn.style.display = 'none';
  initAreaDivValues();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}





async function generatePDFBlob() {
  const response = await fetch("green-calculator-report.html");
  const html = await response.text();
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");


  doc.querySelectorAll(".overview-label").forEach((label, index) => {
    if (inputHeaders[category] && inputHeaders[category][index]) label.textContent = inputHeaders[category][index];
  });


  doc.querySelectorAll(".overview-value").forEach((value, index) => {
    const val = inputData[index] !== undefined ? inputData[index] : "";
    const unit = inputUnits[category] && inputUnits[category][index] ? inputUnits[category][index] : "";
    //value.innerHTML = `${formatNumberPretty(val)} <span>${unit}</span> <br> ${formatNumberPretty(val)} <span>${unit}</span>`;
    value.innerHTML = `${formatNumberPretty(val)} <span>${unit}</span>`;
  });

  doc.querySelectorAll(".impact-section .impact-card .impact-label").forEach((label, index) => {
    if (labels[index]) label.textContent = labels[index];
  });


  doc.querySelectorAll(".impact-section .impact-card .impact-unit").forEach((unitEl, index) => {
    if (units[index] !== undefined) unitEl.textContent = units[index];
  });



  doc.querySelectorAll(".impact-section .impact-card .impact-value").forEach((value, index) => {
    if (ids[index]) value.id = ids[index] + "-value";
  });

  doc.querySelectorAll(".impact-section .impact-card > img").forEach((image, index) => {
    if (iconsToUse[index]) image.src = "https://arkraj7.github.io/csid/Leaf-and-Ledger/images/" + iconsToUse[index];
    //if (iconsToUse[index]) image.src = "./images/" + iconsToUse[index];
    
  });

  doc.querySelector(".section-intro .preview-header").textContent = previewHeaderText;
  doc.querySelector(".section-intro .preview-content").textContent = previewContentText;


  for (const key in calculatedResults) {
    if (!Object.prototype.hasOwnProperty.call(calculatedResults, key)) continue;
    const el = doc.getElementById(key + "-value");
    
    if (el) el.textContent = formatNumberPretty(calculatedResults[key]);
  }
  const now = new Date();
  const formattedDate = now.toLocaleDateString('en-GB').replace(/\//g, '.') + ', ' + now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const dateEl = doc.querySelector("#report-date");
  if (dateEl) dateEl.textContent = formattedDate;
  const reportDiv = doc.getElementById("report");
  if (!reportDiv) return null;
  const cloned = reportDiv.cloneNode(true);
  cloned.style.width = "210mm";
  cloned.style.minHeight = "297mm";
  cloned.style.background = "#fff";
  cloned.style.boxSizing = "border-box";
  document.body.appendChild(cloned);
  const canvas = await html2canvas(cloned, { scale: 2, useCORS: true, backgroundColor: "#ffffff", logging: false });
  const imgData = canvas.toDataURL("image/jpeg", 0.95);
  const pdf = new jspdf.jsPDF("p", "mm", "a4");
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const imgWidth = pageWidth;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;
  let finalHeight, finalWidth;
  if (imgHeight > pageHeight) {
    finalHeight = pageHeight;
    finalWidth = (pageHeight * canvas.width) / canvas.height;
  } else {
    finalHeight = imgHeight;
    finalWidth = imgWidth;
  }
  const xOffset = (pageWidth - finalWidth) / 2;
  const yOffset = (pageHeight - finalHeight) / 2;
  pdf.addImage(imgData, "JPEG", xOffset, yOffset, finalWidth, finalHeight);
  const blob = pdf.output("blob");
  cloned.remove();
  return blob;
}

// --- Data Guide Tab Switching Logic ---
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
  const infoContents = document.querySelectorAll('.tab-info-content');

  tabs.forEach(tab => {
    tab.addEventListener('shown.bs.tab', (event) => {
      // Hide all info contents
      infoContents.forEach(content => {
        content.style.display = 'none';
      });

      // Get the ID of the newly activated tab target
      const targetId = event.target.getAttribute('data-bs-target').replace('#', '');

      // Show the matching info content
      const targetInfo = document.getElementById('info-' + targetId);
      if (targetInfo) {
        targetInfo.style.display = 'block';
      }
    });
  });
});
