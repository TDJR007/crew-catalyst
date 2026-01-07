DECLARE @MyDepartmentList TABLE (
    Number INT  -- Define a column to hold the integers
);


DECLARE @ResourceSubSkillProficiency TABLE (
    ResourceId INT, 
	SubSkillProficiency VARCHAR(MAX)
);


DECLARE @ResourceProjectSubSkills TABLE (
    ProjectId INT, 
    RequirementId INT, 
    ResourceId INT, 
	ResourceProjectSubSkills VARCHAR(MAX)
);


DECLARE @ResourceProjectTotalHours TABLE (
    ProjectId INT, 
    RequirementId INT, 
    ResourceId INT, 
	ResourceProjectTotalHours decimal(18,2)
);

DECLARE @ResourceSubSkillsWithTotalHours TABLE (
    ResourceId INT, 
	ResourceSubSkillsWithTotalHours VARCHAR(MAX)
);


DECLARE @ResourceAvailability TABLE (
    ResourceId INT, 
	ResourceAvailabilityAVGfor3Months decimal(18,2),
	ResourceAvailabilityInPercentage VARCHAR(50)
);

DECLARE @ProjectResourceTotalHours TABLE (
    ProjectId INT, 
    ResourceId INT, 
    TotalHours decimal(18,2)
);
DECLARE @ProjectResourceTotalHoursWithPractice TABLE (
    ProjectId INT, 
    ResourceId INT, 
    TotalHours decimal(18,2),
	CountPracticeIds INT,
	PracticeNames varchar(MAX)
);

DECLARE @ResourcePracticesWithHours TABLE (
    ResourceId INT, 
    PracticeNames varchar(MAX)
);

INSERT INTO @MyDepartmentList (Number) VALUES(85),(86),(87),(88),(89),(94),(70),(74),(93); -- Developers
--INSERT INTO @MyDepartmentList (Number) VALUES(91); -- PM
--INSERT INTO @MyDepartmentList (Number) VALUES(90); -- QA






INSERT INTO @ResourceSubSkillProficiency
SELECT 
	rsa.Resourceid
	--,String_Agg(rsa.SubSkillid, ', ')
	--,String_Agg(rsa.ProficiencyLevel , ', ')
	,String_Agg(Concat(ss.SubSkillName,'(', rsa.ProficiencyLevel,')'), ', ') AS SubSkillProficiency
FROM ResourceSkillAssignment rsa
INNER JOIN SubSkill ss ON rsa.SubSkillid = ss.Id
WHERE rsa.ProficiencyLevel in (4,3,2,1)
GROUP BY rsa.Resourceid

---Resource Practices Strat


INSERT INTO @ProjectResourceTotalHours
SELECT 
		prrsh.ProjectId
		,prrsh.ResourceId
		,Sum(prrsh.TotalHours) as TotalHours
FROM dbo.udf_GetProjectResourceRequirementSkillWithHoursWorked() prrsh
GROUP BY prrsh.ProjectId
		,prrsh.ResourceId

INSERT INTO @ProjectResourceTotalHoursWithPractice
SELECT 
		prth.ProjectId
		,prth.ResourceId
		,prth.TotalHours
		--,pp.PracticeId
		--,p.PracticeName
		,Count(pp.PracticeId) as CountPracticeIds
		--,string_agg(pp.PracticeId,', ') as PracticeIds
		--,string_agg(p.PracticeName,', ') as PracticeNames
		,string_agg(CONCAT(p.PracticeName,' (',CONVERT(DECIMAL(10, 2), prth.TotalHours/pcp.CountPracticeId),')') ,', ') as PracticeNames
FROM @ProjectResourceTotalHours prth
LEFT JOIN (
select distinct ProjectId,PracticeId from ProjectPractice where Active = 1
) pp ON prth.ProjectId = pp.ProjectId
LEFT JOIN (
select ProjectId,Count(PracticeId) as CountPracticeId from ProjectPractice where Active = 1
	GROUP BY ProjectId
) pcp ON prth.ProjectId = pcp.ProjectId
LEFT JOIN Practice p ON pp.PracticeId = p.Id
--WHERE pp.ProjectId = 83
GROUP BY prth.ProjectId
		,prth.ResourceId
		,prth.TotalHours
ORDER BY prth.ResourceId
	

INSERT INTO @ResourcePracticesWithHours
SELECT 
	prthp.ResourceId
	,string_agg(prthp.PracticeNames, ', ') as PracticeNames
FROM @ProjectResourceTotalHoursWithPractice prthp
GROUP BY prthp.ResourceId
		
-- Resource Practices End


INSERT INTO @ResourceProjectSubSkills
SELECT 
	prr.ProjectId
	,prr.Id
	--,prr.DesignationId
	--,pra.Id as praID
	,pra.ResourceId as ResourceId
	--,prrs.SubSkillId
	,ss.SubSkillName
	--,STRING_AGG(ss.SubSkillName,', ') AS ResourceProjectSubSkills
FROM ProjectResourceRequirement prr
INNER JOIN ProjectResourcesRequirementSkill prrs ON prrs.ProjectResourcesRequirementId = prr.Id
INNER JOIN ProjectResourceAllocation pra ON pra.ProjectResourcesRequirementId = prr.Id
INNER JOIN SubSkill ss ON prrs.SubSkillId = ss.Id
--WHERE prr.ProjectId = 12 --and pra.ResourceId = 128
--GROUP BY prr.ProjectId, prr.Id, pra.ResourceId
--ORDER BY prrs.SubSkillId


--ResourceRecentlyWorkedSubSkills

INSERT INTO @ResourceProjectTotalHours
SELECT 
	prr.ProjectId
	,prr.Id
	--,prr.DesignationId
	--,pra.Id as praID
	,pra.ResourceId as ResourceId
	,sum(prwa.WeeklyHours) AS TotalWeeklyHours
	--,prrs.SubSkillId
FROM ProjectResourceRequirement prr
INNER JOIN ProjectResourceAllocation pra ON pra.ProjectResourcesRequirementId = prr.Id
INNER JOIN ProjectResourceWeeklyAllocation prwa ON prwa.ProjectResourceAllocationId = pra.Id
--WHERE prr.ProjectId = 12 --and pra.ResourceId = 128
GROUP BY prr.ProjectId, prr.Id,pra.ResourceId
--ORDER BY prrs.SubSkillId

--select * from @ResourceProjectSubSkills order by ResourceId
--select * from @ResourceProjectTotalHours order by ResourceId


INSERT INTO @ResourceSubSkillsWithTotalHours
SELECT 
	rpss.ResourceId
	--,rpss.ProjectId
	--,rpss.RequirementId
	--,COUNT(rpss.ResourceProjectSubSkills)
	--,sum(rpth.ResourceProjectTotalHours)
	,STRING_AGG(CONCAT(rpss.ResourceProjectSubSkills,'(',rpth.ResourceProjectTotalHours,')'),', ') AS ResourceSubSkillsWithTotalHours
FROM @ResourceProjectSubSkills rpss
INNER JOIN @ResourceProjectTotalHours rpth 
	ON	rpss.ProjectId = rpth.ProjectId AND 
		rpss.RequirementId = rpth.RequirementId AND 
		rpss.ResourceId = rpth.ResourceId 
GROUP BY rpss.ResourceId

--SELECT * FROM @ResourceSubSkillsWithTotalHours





--Availability
DECLARE @NextMonday DATE = DATEADD(DAY, (8 - DATEPART(WEEKDAY, GETDATE())) % 7, GETDATE());

--SELECT 
--    @NextMonday AS StartDate,
--    DATEADD(MONTH, 3, @NextMonday) AS EndDate;

INSERT INTO @ResourceAvailability
SELECT 
	rwa.ResourceId
	,AVG(rwa.Availability)
	--,COUNT(rwa.ResourceId)
	--,SUM(rwa.Availability)/COUNT(rwa.ResourceId)
	,CASE
		WHEN AVG(rwa.Availability) > 30
		THEN '100%'
		ELSE 
				CASE
				WHEN AVG(rwa.Availability) > 20
				THEN '75%'
				ELSE 
						CASE
						WHEN AVG(rwa.Availability) > 10
						THEN '50%'
						ELSE 
								CASE
								WHEN AVG(rwa.Availability) > 0
								THEN '25%'
								ELSE '0%'
								END
						END
				END
		END AS ResourceAvailability
FROM resourceWeeklyAvailability rwa
INNER JOIN Resource r ON rwa.ResourceId = r.Id
WHERE (rwa.WeekDate >= @NextMonday AND rwa.WeekDate < DATEADD(MONTH, 3, @NextMonday)) 
		AND r.Active = 1 
GROUP BY rwa.ResourceId


SELECT 
	r.Id AS ResourceId
	,r.ResourceName AS ResourceName
	,d.DesignationName AS ResourceDesignationName
	,r.ExperienceInMonths AS ResourceExperienceInMonths
	,CONCAT('L',d.DesignationLevel) AS ResourceDesignationLevel
	,dep.DepartmentName AS ResourceDepartmentName
	,CASE
		WHEN basedep.ParentId = 0
		THEN basedep.DepartmentName
		ELSE dep.DepartmentName
	END AS ResourceBaseDepartment
	,rssp.SubSkillProficiency AS ResourceSubSkillWithProficiency
	,rsswth.ResourceSubSkillsWithTotalHours
	,ra.ResourceAvailabilityInPercentage
	,ra.ResourceAvailabilityAVGfor3Months --HoursAvailableOutOf40
	,rph.PracticeNames AS ResourcePracticesWithHoursWorked
FROM [Resource] r 
INNER JOIN Designation d ON r.DesignationId = d.Id
INNER JOIN Department dep ON r.DepartmentId = dep.Id
INNER JOIN @ResourceSubSkillProficiency rssp ON r.Id = rssp.ResourceId
INNER JOIN @ResourceSubSkillsWithTotalHours rsswth ON r.Id = rsswth.ResourceId
INNER JOIN @ResourceAvailability ra ON r.Id = ra.ResourceId
LEFT JOIN Department basedep ON dep.ParentId = basedep.Id
LEFT JOIN @ResourcePracticesWithHours rph ON r.Id = rph.ResourceId
WHERE r.DepartmentId IN (SELECT Number FROM @MyDepartmentList) AND r.Active = 1
ORDER BY r.Id



