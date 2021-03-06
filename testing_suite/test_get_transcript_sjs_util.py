import pytest
import pandas as pd
import os
import subprocess
import sys
from talon.post import get_transcript_sjs as tsj
@pytest.mark.integration

class TestGetTranscriptSJs(object):

    def test_gtf_2_dfs(self):
        """ Create location, edge and transcript data frames from GTF file and 
            make sure they contain the correct entries """
        gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf" 
        ref_loc_df, ref_edge_df, ref_t_df = tsj.create_dfs_gtf(gtf_file)
        print(ref_loc_df)
        run_df_tests(ref_loc_df, ref_edge_df, ref_t_df)

    def test_db_to_dfs(self):
        """ Initialize a TALON database from the same GTF annotation. Then,
            create location, edge and transcript data frames from GTF file and
            make sure they contain the correct entries. """

        os.system("mkdir -p scratch/get_transcript_sjs")
        gtf = "input_files/test_get_transcript_sjs_util/annot.gtf"
        make_database(gtf, "scratch/get_transcript_sjs/talon")
        database = "scratch/get_transcript_sjs/talon.db"
        ref_loc_df, ref_edge_df, ref_t_df = tsj.create_dfs_db(database)
        run_df_tests(ref_loc_df, ref_edge_df, ref_t_df)

    def test_subset_edges(self):
        """ Make sure that this function returns only exons or introns
            as indicated """
        edge_df = pd.DataFrame({'edge_type': ['exon', 'intron'],
                                'strand': ['+', '+'],
                                'v1': [ 0, 1 ], 'v2': [1, 2],
                                'edge_id': [ (0, 1), (1, 2) ],
                                'chrom': ['chr1', 'chr1'],
                                'start': [1, 100],
                                'stop': [100, 500]})

        intron_df = tsj.subset_edges(edge_df, mode='intron')
        exon_df = tsj.subset_edges(edge_df, mode='exon')
        assert len(intron_df) == len(exon_df) == 1
        assert list(intron_df.iloc[0]) == ['intron', '+', 1, 2, (1,2), 'chr1', 100, 500]
        assert list(exon_df.iloc[0]) == ['exon', '+', 0, 1, (0,1), 'chr1', 1, 100]

    def test_determine_sj_novelty_Known_intron(self):
        """ Test that chr1:100-500 gets classified as all known """
        gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
        ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'intron')

        query_gtf = "input_files/test_get_transcript_sjs_util/known.gtf"
        loc_df, edge_df, t_df = prep_gtf(query_gtf, 'intron')

        edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
        assert edge_df.iloc[0].start_known == True
        assert edge_df.iloc[0].stop_known == True
        assert edge_df.iloc[0].combination_known == True

    def test_determine_sj_novelty_Known_exon(self):
        """ Test that chr1:1-100 gets classified as all known """
        gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
        ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'exon')

        query_gtf = "input_files/test_get_transcript_sjs_util/known.gtf"
        loc_df, edge_df, t_df = prep_gtf(query_gtf, 'exon')

        edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
        assert edge_df.iloc[0].start_known == True
        assert edge_df.iloc[0].stop_known == True
        assert edge_df.iloc[0].combination_known == True
       
    def test_determine_sj_novelty_NIC_intron(self):
        """ Test that chr1:100-900 gets classified as having a known start and stop,
            but a novel combination """

        gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
        ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'intron')

        query_gtf = "input_files/test_get_transcript_sjs_util/intron_NIC.gtf"
        loc_df, edge_df, t_df = prep_gtf(query_gtf, 'intron')

        edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
        assert edge_df.iloc[0].start_known == True
        assert edge_df.iloc[0].stop_known == True
        assert edge_df.iloc[0].combination_known == False
        
    def test_determine_sj_novelty_NNC_intron_donor(self):
         """ Test that chr1:90-900 gets classified as having a known stop and
             novel start"""
 
         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'intron')
 
         query_gtf = "input_files/test_get_transcript_sjs_util/intron_NNC_donor.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'intron')
 
         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         assert edge_df.iloc[0].start_known == False
         assert edge_df.iloc[0].stop_known == True
         assert edge_df.iloc[0].combination_known == False

    def test_determine_sj_novelty_NNC_exon_end(self):
         """ Test that chr1:1-90 gets classified as having a known start and
             novel stop"""

         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'exon')

         query_gtf = "input_files/test_get_transcript_sjs_util/intron_NNC_donor.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'exon')

         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         exon = edge_df.loc[edge_df['start'] == 1].iloc[0]
         print(exon)
         assert exon.start_known == True
         assert exon.stop_known == False
         assert exon.combination_known == False    

    def test_determine_sj_novelty_NNC_intron_acceptor(self):
         """ Test that chr1:100-800 gets classified as having a known start and 
             novel stop"""

         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'intron')

         query_gtf = "input_files/test_get_transcript_sjs_util/intron_NNC_acceptor.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'intron')

         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         assert edge_df.iloc[0].start_known == True
         assert edge_df.iloc[0].stop_known == False
         assert edge_df.iloc[0].combination_known == False

    def test_determine_sj_novelty_NNC_exon_start(self):
         """ Test that chr1:800-1000 gets classified as having a known stop and
             novel start"""

         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'exon')

         query_gtf = "input_files/test_get_transcript_sjs_util/intron_NNC_acceptor.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'exon')

         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         exon = edge_df.loc[edge_df['start'] == 800].iloc[0]
         print(exon)
         assert exon.start_known == False
         assert exon.stop_known == True
         assert exon.combination_known == False

    def test_determine_sj_novelty_antisense(self):
         """ Test that chr1:600-1000 on - strand gets classified as all novel"""

         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'intron')

         query_gtf = "input_files/test_get_transcript_sjs_util/intron_novel_antisense.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'intron')

         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         
         assert edge_df.iloc[0].start_known == False
         assert edge_df.iloc[0].stop_known == False
         assert edge_df.iloc[0].combination_known == False

    def test_determine_exon_novelty_antisense(self):
         """ Test that chr1:1-1000 on - strand gets classified as all novel"""

         gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
         ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'exon')

         query_gtf = "input_files/test_get_transcript_sjs_util/antisense_exon.gtf"
         loc_df, edge_df, t_df = prep_gtf(query_gtf, 'exon')
         edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
         exon = edge_df.loc[edge_df['start'] == 100].iloc[0]

         assert edge_df.iloc[0].start_known == False
         assert edge_df.iloc[0].stop_known == False
         assert edge_df.iloc[0].combination_known == False

    def test_transcript_exon_assignment(self):
        """ Test that exon chr1:1-1000 (+) gets assigned only to transcripts
            1 and 2 """
        gtf_file = "input_files/test_get_transcript_sjs_util/annot.gtf"
        ref_loc_df, ref_edge_df, ref_t_df = prep_gtf(gtf_file, 'exon')

        query_gtf = "input_files/test_get_transcript_sjs_util/transcript_exon_assignment.gtf"
        loc_df, edge_df, t_df = prep_gtf(query_gtf, 'exon')
        edge_df = tsj.determine_sj_novelty(ref_edge_df, edge_df)
        edge_df =tsj.find_tids_from_sj(edge_df, t_df, mode = 'exon')
        exon1 = edge_df.loc[(edge_df.chrom == 'chr1') & (edge_df.start == 1)]
        exon2 = edge_df.loc[(edge_df.chrom == 'chr1') & (edge_df.start == 900)]
        exon3 = edge_df.loc[(edge_df.chrom == 'chr1') & (edge_df.start == 100)]
        assert exon1.iloc[0].tids == "test1,test2"
        assert exon2.iloc[0].tids == "test2"
        assert exon3.iloc[0].tids == "antisense"

    def test_full_gtf_mode_intron(self):
        """ Attempt to run the utility from the top in gtf and intron mode.
            Then check that the output file looks as expected. """
        
        try:
            subprocess.check_output(
                ["talon_get_sjs",
                 "--gtf", "input_files/test_get_transcript_sjs_util/transcript_exon_assignment.gtf",
                 "--ref",  "input_files/test_get_transcript_sjs_util/annot.gtf",
                 "--mode", "intron",
                 "--o", "scratch/get_transcript_sjs/full_gtf"])
        except Exception as e:
            print(e)
            sys.exit("talon_get_sjs failed on GTF + intron mode run")
            pytest.fail()

        # Read in and check the file
        data = pd.read_csv("scratch/get_transcript_sjs/full_gtf_introns.tsv",
                           sep='\t', header = 0)
        
        assert data.iloc[0].tolist() == ["chr1", 100, 900, "+", True, True, False, "test2"]
        assert len(data) == 1

    def test_full_gtf_mode_exon(self):
        """ Attempt to run the utility from the top in gtf and exon mode.
            Then check that the output file looks as expected. """

        try:
            subprocess.check_output(
                ["talon_get_sjs",
                 "--gtf", "input_files/test_get_transcript_sjs_util/transcript_exon_assignment.gtf",
                 "--ref",  "input_files/test_get_transcript_sjs_util/annot.gtf",
                 "--mode", "exon",
                 "--o", "scratch/get_transcript_sjs/full_gtf"])
        except Exception as e:
            print(e)
            sys.exit("talon_get_sjs failed on GTF + intron mode run")
            pytest.fail()

        # Read in and check the file
        data = pd.read_csv("scratch/get_transcript_sjs/full_gtf_exons.tsv",
                           sep='\t', header = 0)

        exon1 = data[(data.chrom == 'chr1') & (data.start == 1) & (data.stop == 100)]
        exon2 = data[(data.chrom == 'chr1') & (data.start == 900) & (data.stop == 1000)]
        exon3 = data[(data.chrom == 'chr1') & (data.start == 100) & (data.stop == 1)]
        assert exon1.iloc[0].tolist() == ['chr1', 1, 100, "+", True, True, True, "test1,test2"]
        assert exon2.iloc[0].tolist() == ['chr1', 900, 1000, "+", True, True, True, "test2"]
        assert exon3.iloc[0].tolist() == ['chr1', 100, 1, "-", False, False, False, "antisense"]
        assert len(data) == 3

    def test_full_db_mode_intron(self):
        """ Attempt to run the utility from the top in db and intron mode.
            Then check that the output file looks as expected. """

        os.system("mkdir -p scratch/get_transcript_sjs")
        gtf = "input_files/test_get_transcript_sjs_util/annot.gtf"
        make_database(gtf, "scratch/get_transcript_sjs/talon_intron")
        database = "scratch/get_transcript_sjs/talon_intron.db"

        try:
            subprocess.check_output(
                 ["talon",
                 "--f", "input_files/test_get_transcript_sjs_util/intron_config.csv",
                 "--db", database,
                 "--b", "toy_build", "--cov", "0", "--i", "0", "--o",
                 "scratch/get_transcript_sjs/talon_intron"])
        except Exception as e:
            print(e)
            sys.exit("TALON run failed")
            pytest.fail()

        try:
            subprocess.check_output(
                ["talon_get_sjs",
                 "--db", database,
                 "--ref",  "input_files/test_get_transcript_sjs_util/annot.gtf",
                 "--mode", "intron",
                 "--o", "scratch/get_transcript_sjs/full_db"])
        except Exception as e:
            print(e)
            sys.exit("talon_get_sjs failed on GTF + intron mode run")
            pytest.fail()

        # Read in and check the file
        data = pd.read_csv("scratch/get_transcript_sjs/full_db_introns.tsv",
                           sep='\t', header = 0)

        intron1 = data[(data.chrom == 'chr1') & (data.start == 100) & (data.stop == 500)]
        intron2 = data[(data.chrom == 'chr1') & (data.start == 600) & (data.stop == 900)]
        intron3 = data[(data.chrom == 'chr1') & (data.start == 1500) & (data.stop == 1000)]
        intron4 = data[(data.chrom == 'chr1') & (data.start == 100) & (data.stop == 900)]
        assert intron1.iloc[0].tolist() == ['chr1', 100, 500, "+", True, True, True, "ENST01"]
        assert intron2.iloc[0].tolist() == ['chr1', 600, 900, "+", True, True, True, "ENST01"]
        assert intron3.iloc[0].tolist() == ['chr1', 1500, 1000, "-", True, True, True, "ENST03"]
        assert intron4.iloc[0].tolist() == ["chr1", 100, 900, "+", True, True, False, "TALONT000000004"]
        assert len(data) == 4

    def test_full_db_mode_exon(self):
        """ Attempt to run the utility from the top in db and exon mode.
            Then check that the output file looks as expected.
            Note: the database used is exactly the same as for the intron case,
            hence the 'intron' names. """

        os.system("mkdir -p scratch/get_transcript_sjs")
        gtf = "input_files/test_get_transcript_sjs_util/annot.gtf"
        make_database(gtf, "scratch/get_transcript_sjs/talon_intron")
        database = "scratch/get_transcript_sjs/talon_intron.db"

        try:
            subprocess.check_output(
                 ["talon",
                 "--f", "input_files/test_get_transcript_sjs_util/intron_config.csv",
                 "--db", database,
                 "--b", "toy_build", "--cov", "0", "--i", "0", "--o",
                 "scratch/get_transcript_sjs/talon_intron"])
        except Exception as e:
            print(e)
            sys.exit("TALON run failed")
            pytest.fail()

        try:
            subprocess.check_output(
                ["talon_get_sjs",
                 "--db", database,
                 "--ref",  "input_files/test_get_transcript_sjs_util/annot.gtf",
                 "--mode", "exon",
                 "--o", "scratch/get_transcript_sjs/full_db"])
        except Exception as e:
            print(e)
            sys.exit("talon_get_sjs failed on GTF + intron mode run")
            pytest.fail()

        # Read in and check the file
        data = pd.read_csv("scratch/get_transcript_sjs/full_db_exons.tsv",
                           sep='\t', header = 0)

        exon1 = data[(data.chrom == 'chr1') & (data.start == 1) & (data.stop == 100)]
        exon2 = data[(data.chrom == 'chr1') & (data.start == 500) & (data.stop == 600)]
        exon3 = data[(data.chrom == 'chr1') & (data.start == 900) & (data.stop == 1000)]
        exon4 = data[(data.chrom == 'chr4') & (data.start == 4000) & (data.stop == 1000)]
        exon5 = data[(data.chrom == 'chr1') & (data.start == 2000) & (data.stop == 1500)]
        exon6 = data[(data.chrom == 'chr1') & (data.start == 1000) & (data.stop == 900)]
        exon7 = data[(data.chrom == 'chr1') & (data.start == 100) & (data.stop == 1)]
        assert exon1.iloc[0].tolist() == ['chr1', 1, 100, "+", True, True, True, "ENST01,TALONT000000004"]
        assert exon2.iloc[0].tolist() == ['chr1', 500, 600, "+", True, True, True, "ENST01"]
        assert exon3.iloc[0].tolist() == ['chr1', 900, 1000, "+", True, True, True, "ENST01,TALONT000000004"]
        assert exon4.iloc[0].tolist() == ["chr4", 4000, 1000, "-", True, True, True, "ENST07"]
        assert exon5.iloc[0].tolist() == ["chr1", 2000, 1500, "-", True, True, True, "ENST03"]
        assert exon6.iloc[0].tolist() == ["chr1", 1000, 900, "-", True, True, True, "ENST03"]
        assert exon7.iloc[0].tolist() == ["chr1", 100, 1, "-", False, False, False, "TALONT000000005"]
        assert len(data) == 7

def make_database(gtf, prefix):
    """ Wrapper to init TALON database """
    try:
        existing_db = prefix + ".db"
        os.remove(existing_db)
    except:
        pass

    try:
        subprocess.check_output(
            ["talon_initialize_database",
             "--f", gtf,
             "--a",  "toy_annot",
             "--l", "0",
             "--g",  "toy_build", "--o", prefix])
    except Exception as e:
        print(e)
        sys.exit("Database initialization failed on toy annotation")
    return

def prep_gtf(gtf, mode):
    """ Wrapper for GTF processing steps used by get_transcript_sjs main """
    loc_df, edge_df, t_df = tsj.create_dfs_gtf(gtf)
    edge_df = tsj.add_coord_info(edge_df, loc_df)
    edge_df = tsj.subset_edges(edge_df, mode=mode)
    edge_df = tsj.format_edge_df(edge_df)

    return loc_df, edge_df, t_df
        
def run_df_tests(ref_loc_df, ref_edge_df, ref_t_df):
    """ Runs the location, edge, and transcript tests on dfs """
    # Make sure the correct positions made it into the location df
    expected_locs = [("chr1", 1), ("chr1", 100), ("chr1", 500), 
                     ("chr1", 600), ("chr1", 900), ("chr1", 1000), 
                     ("chr4", 1000), ("chr4", 4000), 
                     ("chr1", 1500), ("chr1", 2000)]
    assert len(ref_loc_df) == len(expected_locs)

    for item in expected_locs:
        chrom = item[0]
        loc = item[1]
        assert ((ref_loc_df.chrom == chrom) & (ref_loc_df.coord == loc)).any()

    # Make sure that the correct edges are in the edge df
    assert len(ref_edge_df.loc[ref_edge_df.edge_type == 'intron']) == 3
    assert len(ref_edge_df.loc[ref_edge_df.edge_type == 'exon']) == 6

    # Check that the transcript position paths are correct across the tables
    expected_paths = {"ENST01": [1, 100, 500, 600, 900, 1000],
                      "ENST07": [4000, 1000],
                      "ENST03": [2000, 1500, 1000, 900]}
    for tid in ["ENST01", "ENST07", "ENST03"]:
        v_path = list(ref_t_df.loc[ref_t_df.tid == tid].path)[0]
        pos_path = []
        for vertex in v_path :
            pos = int(ref_loc_df.loc[ref_loc_df.vertex_id == vertex].coord)
            pos_path.append(pos)
        assert pos_path == expected_paths[tid]
