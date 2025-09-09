import React from "react";
import LeadsCard from "./LeadsCard";
import PieChartComponent from "./PieChartComponent";
import HourlyHeatmap from "./HeatMap";
import TrendAnalysisComponent from "./TrendAnalysisComponent";
const AnalyticsDashboard = () => (
  <>
    <div className="lg:flex lg:flex-col-2 md:flex-row-2 mt-10 mx-auto gap-10 sm:flex-row-2 sm:gap-10">
    <PieChartComponent />
    <TrendAnalysisComponent />
  </div>
  <div className="flex flex-col   mt-10 mx-auto">
    <LeadsCard />
  </div>

  <div className="flex flex-col mt-10 mx-auto">
    <HourlyHeatmap  />
  </div>
  </>
);

export default AnalyticsDashboard; 