SELECT
    f.jkey,
    f.summary,
    
    bxtmm.jkey,
    bxtmm.priority,
    bxtmm.status,
    
    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status
   
FROM
    (SELECT * FROM areq_e_features WHERE platform = 'Broxton' and version = 'M') as bxtmm
    INNER JOIN areq_features f
        ON (bxtmm.feature_jkey = f.jkey)
    LEFT OUTER JOIN (
        SELECT * from areq_e_features WHERE platform = 'Broxton-P IVI' AND version = 'M') AS bxtpm
    ON (bxtmm.feature_jkey = bxtpm.feature_jkey)
WHERE
    bxtmm.priority like 'P1%'
    AND bxtmm.rejected = 0
    AND (IFNULL(bxtpm.rejected,1) = 1 OR IFNULL(bxtpm.priority, bxtmm.priority) != bxtmm.priority)
ORDER BY
	f.summary
;
