SELECT
    bxtpm.global_id,
    bxtpm.jkey,
    bxtpm.summary,
    bxtpm.priority,
    bxtpm.status,
    
    bxtmm.jkey,
    bxtmm.priority,
    bxtmm.status
FROM
    (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' AND version = 'M') AS bxtpm
    LEFT OUTER JOIN
        (SELECT * FROM preq_features WHERE platform = 'Broxton' and version = 'M') AS bxtmm
    ON (bxtpm.global_id = bxtmm.global_id)
WHERE
    bxtpm.priority like 'P1%'
    AND bxtpm.rejected = 0
    AND (IFNULL(bxtmm.rejected,1) = 1 OR IFNULL(bxtmm.priority, bxtpm.priority) != bxtpm.priority)
ORDER BY bxtpm.summary

;
