import dcm2niix
import os
import sys
import subprocess
import SimpleITK as sitk
import argparse
import numpy as np
import nibabel as nib


def nibSaveNifti(data, affine, hd, fname):
    # If nifty1
    if hd['sizeof_hdr'] == 348:
        new_image = nib.Nifti1Image(data, affine, header=hd)
    # If nifty2
    elif hd['sizeof_hdr'] == 540:
        new_image = nib.Nifti2Image(data, affine, header=hd)
    else:
        raise IOError('Input image header problem')
    
    nib.save(new_image, fname)

def copy_file(src_file, dest_file):
    with open(src_file, 'rb') as file:
        content = file.read()
    with open(dest_file, 'wb') as otherfile:
        otherfile.write(content)

def isTypeShort(fname):
    image = nib.load(fname)
    return image.header.get_data_dtype() == "int16"

def nii2short(fname):
    if isTypeShort(fname):
        return
    
    image = nib.load(fname)
    new_data = np.copy(image.get_fdata())
    
    # Change to data type to short:
    new_dtype = np.int16
    new_data = new_data.astype(new_dtype)
    image.set_data_dtype(new_dtype)

    nibSaveNifti(new_data, image.affine, image.header, fname)

def shortify_nifti(indir):
    for fof in os.listdir(indir):
        loop_indir = os.path.join(indir, fof)
        if os.path.isdir(loop_indir):
            shortify_nifti(loop_indir)
        elif fof.find('.nii') != -1:
            nii2short(loop_indir)


# Decapitate bottom 'remove_fac' percent of slices
def decapitate_nifti_file(in_fname, out_fname,  remove_fac):
    image = nib.load(in_fname)
    new_data = np.copy(image.get_fdata())

    affine = image.affine
    voxel_sizes = image.header.get_zooms()
    translation_matrix = np.zeros((4,4))
    np.fill_diagonal(translation_matrix, 1)

    orientation = nib.aff2axcodes(affine)

    remove_fac = remove_fac / 100.
    if 'I' in orientation:
        decap_axis = orientation.index('I')
        n_slices = new_data.shape[decap_axis]
        n_remove = int(n_slices*remove_fac)
        offset = int(n_remove / 2)
        match decap_axis:
            case 0:
                new_data[-n_remove:, :, :] = 0
                new_data[offset:, :, :] = new_data[:-offset, :, :]
                new_data[:offset, :, :] = 0
                translation_matrix[0, 3] = -offset*voxel_sizes[0]
            case 1:
                new_data[:, -n_remove:, :] = 0
                new_data[:, offset:, :] = new_data[:, :-offset, :]
                new_data[:, :offset, :] = 0
                translation_matrix[1, 3] = -offset*voxel_sizes[1]
            case 2:
                new_data[:, :, -n_remove:] = 0
                new_data[:, :, offset:] = new_data[:, :, :-offset]
                new_data[:, :, :offset] = 0
                translation_matrix[2, 3] = -offset*voxel_sizes[2]


    elif 'S' in orientation:
        decap_axis = orientation.index('S')
        n_slices = new_data.shape[decap_axis]
        n_remove = int(n_slices*remove_fac)
        offset = int(n_remove / 2)
        match decap_axis:
            case 0:
                new_data[:n_remove, :, :] = 0
                new_data[:-offset, :, :] = new_data[offset:, :, :]
                new_data[-offset:, :, :] = 0
                translation_matrix[0, 3] = offset*voxel_sizes[0]
            case 1:
                new_data[:, :n_remove, :] = 0
                new_data[:, :-offset, :] = new_data[:, offset:, :]
                new_data[:, -offset:, :] = 0
                translation_matrix[1, 3] = offset*voxel_sizes[1]
            case 2:
                new_data[:, :, :n_remove] = 0
                new_data[:, :, :-offset] = new_data[:, :, offset:]
                new_data[:, :, -offset:] = 0
                translation_matrix[2, 3] = offset*voxel_sizes[2]

    new_affine = np.dot(affine, translation_matrix)
    nibSaveNifti(new_data, new_affine, image.header, out_fname)

def run_decapitate(indir, outdir, remove_fac):
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    for fof in os.listdir(indir):
        loop_indir = os.path.join(indir, fof)
        loop_outdir = os.path.join(outdir, fof)
        if os.path.isdir(loop_indir):
            run_decapitate(loop_indir, loop_outdir, remove_fac)
        
        elif fof.find('.nii') != -1:
            print("Decapitating bottom %d%% of slices on file:" % (remove_fac), loop_indir)
            decapitate_nifti_file(loop_indir, loop_outdir, remove_fac)


# DICOM to nifti funcs
def contains_files_only(indir):
    for fof in os.listdir(indir):
        if os.path.isdir(os.path.join(indir, fof)):
            return False
    return True

def dcm2nii(indir, outdir, do_zip):
    # List before adding outdir if outdir is subfolder of indir
    dir_content = os.listdir(indir)

    if not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    for fof in dir_content:
        loop_indir = os.path.join(indir, fof)
        loop_outdir = os.path.join(outdir, fof)
        if not os.path.isdir(loop_indir):
            continue

        if contains_files_only(loop_indir):
            if os.path.exists(loop_outdir+".nii.gz"):
                os.remove(loop_outdir+".nii.gz")
            elif os.path.exists(loop_outdir+".nii"):
                    os.remove(loop_outdir+".nii")

            if do_zip:
                dcm2niix.main(["-f", "%f", "-z", "o", "-o", outdir, loop_indir])
            else:
                dcm2niix.main(["-f", "%f", "-o", outdir, loop_indir])
        else:
            dcm2nii(loop_indir, loop_outdir, do_zip)


# ACPC Alignment funcs
def run_acpc_on_file_nii(input_file):
    subprocess.run([os.path.join(os.getcwd(), "src", "run_acpcdetect.sh"), "-i", input_file])

def run_acpc(indir, outdir):
     # List before adding outdir if outdir is subfolder of indir
    dir_content = os.listdir(indir)

    if not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    for fof in dir_content:
        loop_indir = os.path.join(indir, fof)
        loop_outdir = os.path.join(outdir, fof)
        if os.path.isdir(loop_indir):
            run_acpc(loop_indir, loop_outdir)
        
        elif fof.find('.nii') != -1:
            fname_wo_ext = fof[:fof.find('.nii')]
            fof_outdir = os.path.join(outdir, fname_wo_ext)
            if not os.path.exists(fof_outdir):
                os.mkdir(fof_outdir)
                
            loop_outdir = os.path.join(fof_outdir, fof)
            copy_file(loop_indir, loop_outdir)
            if not isTypeShort(loop_outdir):
                nii2short(loop_outdir)

            print("Running ACPC alignment on file:", loop_indir)
            run_acpc_on_file_nii(loop_outdir)
            os.remove(loop_outdir)


# Bias field correction funcs
def run_bfc_on_file_nii(input_file, output_file, shrink_fac):
    
    orig_input_img = sitk.ReadImage(input_file, sitk.sitkFloat32)
    
    head_mask = sitk.RescaleIntensity(orig_input_img, 0, 255)
    head_mask = sitk.LiThreshold(head_mask, 0, 1)

    pre_corrected_img = sitk.Shrink(orig_input_img, [shrink_fac] * orig_input_img.GetDimension())
    pre_corrected_mask = sitk.Shrink(head_mask, [shrink_fac] * orig_input_img.GetDimension())

    bias_corrector = sitk.N4BiasFieldCorrectionImageFilter()
    _ = bias_corrector.Execute(pre_corrected_img, pre_corrected_mask)

    log_bias_field = bias_corrector.GetLogBiasFieldAsImage(orig_input_img)
    corrected_image_full_resolution = orig_input_img / sitk.Exp(log_bias_field)

    nib_image = nib.load(input_file)
    match nib_image.header.get_data_dtype():
        case "int16":
            corrected_image_full_resolution = sitk.Cast(corrected_image_full_resolution, sitk.sitkInt16)
        case "int32":
            corrected_image_full_resolution = sitk.Cast(corrected_image_full_resolution, sitk.sitkInt32)
        case "int64":
            corrected_image_full_resolution = sitk.Cast(corrected_image_full_resolution, sitk.sitkInt64)
        case "float32":
            corrected_image_full_resolution = sitk.Cast(corrected_image_full_resolution, sitk.sitkFloat32)
        case "float64":
            corrected_image_full_resolution = sitk.Cast(corrected_image_full_resolution, sitk.sitkFloat64)

    sitk.WriteImage(corrected_image_full_resolution, output_file)

def run_bfc(indir, outdir, shrink_fac):
    # List before adding outdir if outdir is subfolder of indir
    dir_content = os.listdir(indir)

    if not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    for fof in dir_content:
        loop_indir = os.path.join(indir, fof)
        loop_outdir = os.path.join(outdir, fof)
        if os.path.isdir(loop_indir):
            run_bfc(loop_indir, loop_outdir, shrink_fac)
        elif fof.find('.nii') != -1:
            fname_wo_ext = fof[:fof.find('.nii')]
            out_fname_wo_ext = os.path.join(outdir, fname_wo_ext)
            if os.path.exists(out_fname_wo_ext+".nii"):
                os.remove(out_fname_wo_ext+".nii")
            elif os.path.exists(out_fname_wo_ext+".nii.gz"):
                os.remove(out_fname_wo_ext+".nii.gz")
                
            print("Running bias field correction on file:", loop_indir)
            run_bfc_on_file_nii(loop_indir, loop_outdir, shrink_fac)



# Main func
def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--inDir', help="Directory of input data to perform actions on.", required=True)
    parser.add_argument('-o', '--outDir', help="Directory to save output data into.", required=True)
    parser.add_argument('-z', '--doZip', help="Save nifti images as compressed files (.nii.gz).", action='store_true')
    parser.add_argument('--do', help="Specify which processing steps to do. Possible options are:\n'n' - dcm to nifti conversion.\n'b' - Bias field correction.\n'a' - ACPC alignment.\nDefault option is 'n'. Multiple steps can be specified by writing a sequence of options, e.g. 'nab',\nwhere the steps are performed in the order of the string.", default='n')
    parser.add_argument('--decap', help="Usage: --decap <fac>. Will 'decapitate' volume by setting bottom <fac> percent of slices to 0. Is performed prior to ACPC alignment.", type=float)
    parser.add_argument('--bfcFac', help="Shrink factor for bias field correction. Computes correction on a lower resolution image shrunken by <bfcFac> in all directions to reduce computational load and increased speed, at the expense of accuracy.", type=int, default=4)

    args = parser.parse_args()

    pipeline_input = args.inDir
    pipeline_output = args.outDir

    if not os.path.isdir(pipeline_input):
        print("Input directory not found. Program terminated!")
        return
    
    #if not os.path.isdir(pipeline_output):
    #    os.mkdir(pipeline_output)
    #    print("Output directory created")

    proc_order = args.do
    done_opts = ""
    for opt in proc_order:
        match opt:
            case 'n' if opt not in done_opts:
                nifti_dir = os.path.join(pipeline_output, "nifti")    
                dcm2nii(pipeline_input, nifti_dir, args.doZip)
                pipeline_input = nifti_dir
                done_opts += opt

            case 'a' if opt not in done_opts:
                # Check if decapitation flag is set
                if args.decap:
                    decap_dir = os.path.join(pipeline_output, "decap") 
                    run_decapitate(pipeline_input, decap_dir, args.decap)
                    pipeline_input = decap_dir

                # Run ACPC
                acpc_dir = os.path.join(pipeline_output, "acpc")
                run_acpc(pipeline_input, acpc_dir)
                pipeline_input = acpc_dir
                done_opts += opt

            case 'b' if opt not in done_opts:
                bfc_dir = os.path.join(pipeline_output, "bfc")
                run_bfc(pipeline_input, bfc_dir, args.bfcFac)
                pipeline_input = bfc_dir
                done_opts += opt
            case _:
                print("Ignoring unkown processing option '%s'." % (opt))



if __name__ == '__main__':
    sys.exit(main())


